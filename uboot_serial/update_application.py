"""
update_application.py
This script updates the application on the device taken from the microSD card.
"""

import argparse
import serial
import serial.tools.list_ports
from uboot import read_until, readline_until, send_cmd, check_prompt, log, \
    boot_to_login, boot_to_root

def main():
    """
    Main function. Executed when run from command line.
    """
    in_arg = get_input_args()

    # validate inputs
    if in_arg.port == "":
        # scan for FTDI com ports by vendor ID = 0x0403
        usb_serial_ports = []
        for port in serial.tools.list_ports.grep("0403"):
            usb_serial_ports.append(port.device)
        if usb_serial_ports == []:
            # no devices found
            print("Could not find an FTDI connected device.")
            print("Please connect an FTDI USB-to-serial converter " \
                  "or specify the port with the --port option.")
            print("Exiting script...")
            raise RuntimeError("Could not find an FTDI connected device.")
        if len(usb_serial_ports) > 1:
            # found multiple devices
            print("Found multiple FTDI devices: {}".format(usb_serial_ports))
            print("Please use the --port option to select the correct device.")
            print("Exiting script...")
            raise RuntimeError("Found multiple FTDI devices: {}".format(usb_serial_ports))
        ftdi_port = usb_serial_ports[0]
    else:
        ftdi_port = in_arg.port

    # run script
    update_application(ftdi_port, in_arg.serialno, in_arg.root_psswd)

def update_application(port, serialno, root_psswd="Allergen_lock"):
    """
    update_application function
    This function updates the application on the device from the microSD card.
    The procedure is as follows:
    1. boot to root prompt
    2. mount SD card
    3. copy application setup file
    4. run application setup
    5. reboot back to login prompt

    Parameters
        port                The COM port on which the FTDI serial device is connected.
                            On Windows machines, this will be the word COM followed by
                            a port number.
        serialno            Required serial number of the device to be programmed.
        root_psswd          The new root password if other than the default.
                            default=Allergen_lock

    Returns
        passphrase          Returns the computed passphrase for the device.
    """
    print_log = False
    if __name__ == '__main__':
        print_log = True

    # validate inputs
    if not isinstance(serialno, str):
        raise TypeError("Serial Number must be an alpha-numeric string type.")
    if not isinstance(root_psswd, str):
        raise TypeError("Root password must be string type.")
    if len(serialno) != 16:
        raise ValueError("Serial Number must be 16 characters.")
    if not serialno[-8:].isdigit():
        raise ValueError("Last 8 characters of Serial Number must be numeric.")
    if not serialno[:8].isupper():
        raise ValueError("First 8 characters of Serial Number must be " \
                         "uppercase alpha-numeric.")
    try:
        com = serial.Serial(port, 115200, timeout=1)
    except serial.SerialException as err:
        log("Could not access comport {}".format(port), print_log)
        log("Exiting script...", print_log)
        raise serial.SerialException(err)

    # Check prompt to find where we're at
    prompt = check_prompt(com)

    # If no prompt, then tell user to boot the device
    if prompt == "":
        log("Please power ON or RESET the device now...", print_log)
        result = readline_until(com, "U-Boot", timeout=60)
        if not result:
            log("Request timed out...", print_log)
            log("Exiting script...", print_log)
            com.close()
            raise RuntimeError("Request timed out...")
        log("Booting to root prompt...", print_log)
        read_until(com, "ccimx6sbc login: ", timeout=40)
        boot_to_root(com, reboot=False)
        log("At root prompt...", print_log)

    # If prompt is already at root, don't reboot.
    elif prompt == "root":
        log("At root prompt...", print_log)
    # Otherwise, reboot and stop at root prompt
    else:
        log("Booting to root prompt...", print_log)
        boot_to_root(com, reboot=False)
        log("At root prompt...", print_log)

    # mount SD card
    log("Mounting SD card...", print_log)
    send_cmd(com, "mkdir /mnt/sdc")
    readline_until(com, "#")
    send_cmd(com, "mount -t vfat /dev/mmcblk1p1 /mnt/sdc")
    readline_until(com, "mount -t vfat /dev/mmcblk1p1 /mnt/sdc")
    result = readline_until(com, "#")
    if "failed" in result:
        log("Failure!", print_log)
        log("Failed to mount SD card.", print_log)
        log("Exiting script...", print_log)
        com.close()
        raise RuntimeError("Failed to mount SD card.")

    # copy application setup file
    log("Copying application setup files...", print_log)
    send_cmd(com, "cp /mnt/sdc/Setup.sh ./")
    readline_until(com, "#")
    send_cmd(com, "chmod 777 Setup.sh")
    readline_until(com, "#")

    # run application setup
    log("Installing application...", print_log)
    send_cmd(com, "./Setup.sh")
    result = readline_until(com, "Setting Serial Number")
    if "No such file or directory" in result:
        log("Failure!", print_log)
        log("Failed to install application. Directory not found.", print_log)
        log("Exiting script...", print_log)
        com.close()
        raise RuntimeError("Failed to install application. Directory not found.")
    readline_until(com, "Enter New Serial Number")
    log("Programming serial number {}...".format(serialno), print_log)
    send_cmd(com, serialno)
    readline_until(com, "Computed PassPhrase:")
    passphrase = com.readline().decode('ascii')
    log("Computed passphrase: {}".format(passphrase), print_log)
    read_until(com, "New password: ")
    log("Entering new root password {}...".format(root_psswd), print_log)
    send_cmd(com, root_psswd)
    read_until(com, "Re-enter new password: ")
    send_cmd(com, root_psswd)
    read_until(com, "#")

    # reboot back to login prompt
    log("Rebooting...", print_log)
    booted = boot_to_login(com, reboot=True)
    if booted:
        log("Application update is complete.", print_log)
    else:
        log("Failure!", print_log)
        log("Failed to boot kernel.", print_log)
        log("Exiting script...", print_log)
        com.close()
        raise RuntimeError("Failed to boot kernel.")

    com.close()
    return passphrase

def get_input_args():
    """
    Parse command line arguments.

    usage: update_application.py [-h] [--port PORT] [--root_psswd PASSWORD] serialno

    positional arguments:
        serialno                    The new serial number to be flashed on the device.

    optional arguments:
        -h, --help                  show this help message and exit
        --port PORT                 The COM port on which the FTDI serial device is connected.
                                    On Windows machines, this will be the word COM followed by
                                    a port number. By default, this script scans for FTDI
                                    devices and selects one if available.
        --root_psswd PASSWORD       The new root password if other than the default.
                                    default=Allergen_lock

    Parameters:
        none
    Returns:
        parse_args() - data structure that stores the command line arguments object
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('serialno', action="store", type=str,
                        help='The new serial number to be flashed on the device.')
    parser.add_argument('--port', action="store", type=str, default="",
                        help='The COM port on which the FTDI serial device is ' \
                            'connected. On Windows machines, this will be the ' \
                            'word COM followed by a port number. ' \
                            'By default, this script scans for FTDI devices ' \
                            'and selects one if available.')
    parser.add_argument('--root_psswd', action="store", type=str,
                        default='Allergen_lock',
                        help='The new root password if other than the default. ' \
                             'default=Allergen_lock')
    return parser.parse_args()

if __name__ == '__main__':
    main()
