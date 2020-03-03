"""
update_bootloader.py
This script updates the bootloader image on the u-boot device taken from the microSD card.
"""

import argparse
import serial
import serial.tools.list_ports
from uboot import read_until, readline_until, send_cmd, check_prompt, boot_to_uboot, log

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
    update_bootloader(ftdi_port, in_arg.image)

def update_bootloader(port, image, log_widget=None):
    """
    update_bootloader function
    This function updates the bootloader from the image on the microSD card.
    The procedure is as follows:
    1. Reboot the device to stop at u-boot prompt.
       If no prompt is found, the user is asked to boot the device from the SD card.
    2. Program the bootloader on the device from image on card.
    3. Reset the CPU and come up to new u-boot prompt.

    Parameters
        port                The COM port on which the FTDI serial device is connected.
                            On Windows machines, this will be the word COM followed by
                            a port number.
        image               The name of the u-boot image file to be flashed
        log_widget          The tkinter scrolled text object for printing log output to GUI.
                            Only used by GUI. Default is None when called by command line.

    Returns
        none
    """
    print_log = False
    if __name__ == '__main__':
        print_log = True

    # validate inputs
    if image[-4:] != ".imx":
        raise ValueError("Image file extension must be *.imx")
    try:
        com = serial.Serial(port, 115200, timeout=1)
    except serial.SerialException as err:
        log("Could not access comport {}".format(port), print_log, log_widget)
        log("Exiting script...", print_log, log_widget)
        raise serial.SerialException(err)

    # Check prompt to find where we're at
    prompt = check_prompt(com)

    # If no prompt, then tell user to boot from SD card
    if prompt == "":
        log("Please boot the device via the SD card now...", print_log, log_widget)
        result = read_until(com, "Hit any key to stop autoboot: ", timeout=60)
        if result:
            send_cmd(com, "")
            prompt = check_prompt(com)
            if prompt == "uboot":
                log("You may release the programming button now...", print_log, log_widget)
        else:
            log("Request timed out...", print_log, log_widget)
            log("Exiting script...", print_log, log_widget)
            com.close()
            raise RuntimeError("Request timed out...")
    # If prompt is already at u-boot, don't reset.
    elif prompt == "uboot":
        log("At u-boot prompt...", print_log, log_widget)
    # Otherwise, reset and stop at u-boot prompt
    else:
        log("Booting to u-boot prompt...", print_log, log_widget)
        boot_to_uboot(com, reset=True)

    # Program the bootloader
    log("Programming the bootloader...", print_log, log_widget)
    command = "update uboot mmc 1 fat " + image
    send_cmd(com, command)
    read_until(com, "program the boot loader? <y/N>")
    send_cmd(com, "y")
    result = readline_until(com, "=>")
    if "Update was successful" in result:
        log("Success!", print_log, log_widget)
        log("Bootloader updated successfully.", print_log, log_widget)
    else:
        log("Failure!", print_log, log_widget)
        if "Error loading firmware file to RAM." in result:
            log("Could not find u-boot image file {} on SD card, " \
                "or card is not present.".format(image), print_log, log_widget)
        log("Exiting script...", print_log, log_widget)
        com.close()
        raise RuntimeError("Error loading firmware file to RAM.")

    # Reset and stop at u-boot prompt
    log("Resetting CPU and booting to u-boot prompt...", print_log, log_widget)
    boot_to_uboot(com, reset=True)

    com.close()
    log("Bootloader update is complete.", print_log, log_widget)

def get_input_args():
    """
    Parse command line arguments.

    usage: update_bootloader.py [-h] [--port PORT] [--image IMAGE]

    positional arguments:
        none

    optional arguments:
        -h, --help          show this help message and exit
        --port PORT         The COM port on which the FTDI serial device is connected.
                            On Windows machines, this will be the word COM followed by
                            a port number. By default, this script scans for FTDI
                            devices and selects one if available.
        --image IMAGE       The name of the u-boot image file to be flashed;
                            default=u-boot-ccimx6qsbc.imx

    Parameters:
        none
    Returns:
        parse_args() - data structure that stores the command line arguments object
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', action="store", type=str, default="",
                        help='The COM port on which the FTDI serial device is ' \
                            'connected. On Windows machines, this will be the ' \
                            'word COM followed by a port number. ' \
                            'By default, this script scans for FTDI devices ' \
                            'and selects one if available.')
    parser.add_argument('--image', action="store", type=str, default='u-boot-ccimx6qsbc.imx',
                        help='The name of the u-boot image file to be flashed; ' \
                             'default=u-boot-ccimx6qsbc.imx')
    return parser.parse_args()

if __name__ == '__main__':
    main()
