"""
update_kernel.py
This script updates the Yocto kernel images on the device taken from the microSD card.
"""

import argparse
import serial
import serial.tools.list_ports
from uboot import read_until, readline_until, send_cmd, check_prompt, boot_to_uboot, log, \
    boot_to_login

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
            return
        if len(usb_serial_ports) > 1:
            # found multiple devices
            print("Found multiple FTDI devices: {}".format(usb_serial_ports))
            print("Please use the --port option to select the correct device.")
            print("Exiting script...")
            return
        ftdi_port = usb_serial_ports[0]
    else:
        ftdi_port = in_arg.port

    # run script
    update_kernel(ftdi_port, in_arg.boot_image, in_arg.rootfs_image, in_arg.recovery_image)

def update_kernel(port, boot_image, rootfs_image, recovery_image):
    """
    update_kernel function
    This function updates the Yocto kernel from the images on the microSD card.
    The procedure is as follows:
    1. boot to u-boot prompt
    2. partition eMMC drive
    3. reset back to u-boot prompt
    4. update images
    5. update environments
    6. boot to login prompt

    Parameters
        port                The COM port on which the FTDI serial device is connected.
                            On Windows machines, this will be the word COM followed by
                            a port number.
        boot_image          The name of the boot image file to be flashed
        rootfs_image        The name of the rootfs image file to be flashed
        recovery_image      The name of the recovery image file to be flashed
    Returns
        none
    """
    print_log = False
    if __name__ == '__main__':
        print_log = True

    # validate inputs
    if boot_image[-10:] != ".boot.vfat":
        raise ValueError("BOOT image file extension must be *.boot.vfat")
    if rootfs_image[-12:] != ".rootfs.ext4":
        raise ValueError("ROOTFS image file extension must be *.rootfs.ext4")
    if recovery_image[-14:] != ".recovery.vfat":
        raise ValueError("RECOVERY image file extension must be *.recovery.vfat")
    try:
        com = serial.Serial(port, 115200, timeout=1)
    except serial.SerialException:
        log("Could not access comport {}".format(port), print_log)
        log("Exiting script...", print_log)
        return

    # Check prompt to find where we're at
    prompt = check_prompt(com)

    # If no prompt, then tell user to boot the device
    if prompt is None:
        log("Please power ON or RESET the device now...", print_log)
        result = read_until(com, "Hit any key to stop autoboot: ", timeout=60)
        if result:
            send_cmd(com, "")
        else:
            log("Request timed out...", print_log)
            log("Exiting script...", print_log)
            com.close()
            return
    # Stop at u-boot prompt
    else:
        log("Booting to u-boot prompt...", print_log)
        boot_to_uboot(com)

    # partition eMMC
    log("Partitioning eMMC drive...", print_log)
    send_cmd(com, "setenv mmcdev 0")
    readline_until(com, "=>")
    send_cmd(com, "env default -a -f")
    readline_until(com, "=>")
    send_cmd(com, "run partition_mmc_linux")
    result = readline_until(com, "=>")
    if "Writing GPT: success!" in result:
        log("Success!", print_log)
        log("Flash eMMC partitioned successfully.", print_log)
    else:
        log("Failure!", print_log)
        log("Flash eMMC could not be partitioned.", print_log)
        log("Exiting script...", print_log)
        com.close()
        return
    send_cmd(com, "setenv mmcdev 0")
    readline_until(com, "=>")

    # reset back to u-boot prompt
    log("Resetting CPU to u-boot prompt...", print_log)
    boot_to_uboot(com)

    # update images
    log("Updating linux boot file...", print_log)
    command = "update linux mmc 1 fat " + boot_image
    send_cmd(com, command)
    result = readline_until(com, "=>", timeout=30)
    if "Update was successful" in result:
        log("Success!", print_log)
        log("Linux installed successfully.", print_log)
    else:
        log("Failure!", print_log)
        log("Linux could not be installed.", print_log)
        log("Exiting script...", print_log)
        com.close()
        return

    log("Updating root file system. This may take up to two minutes...", print_log)
    command = "update rootfs mmc 1 fat " + rootfs_image
    send_cmd(com, command)
    result = readline_until(com, "=>", timeout=120)
    if "Firmware updated" in result:
        log("Success!", print_log)
        log("Root file system installed successfully.", print_log)
    else:
        log("Failure!", print_log)
        log("Root file system could not be installed.", print_log)
        log("Exiting script...", print_log)
        com.close()
        return

    log("Updating recovery image...", print_log)
    command = "update recovery mmc 1 fat " + recovery_image
    send_cmd(com, command)
    result = readline_until(com, "=>", timeout=30)
    if "Update was successful" in result:
        log("Success!", print_log)
        log("Recovery image installed successfully.", print_log)
    else:
        log("Failure!", print_log)
        log("Recovery image could not be installed.", print_log)
        log("Exiting script...", print_log)
        com.close()
        return

    # update environments
    log("Updating environments...", print_log)
    send_cmd(com, "setenv bootcmd dboot linux mmc")
    readline_until(com, "=>")
    send_cmd(com, "saveenv")
    readline_until(com, "=>")
    send_cmd(com, "setenv mmcdev 0")
    readline_until(com, "=>")
    send_cmd(com, "env default -a -f")
    readline_until(com, "=>")
    send_cmd(com, "saveenv")
    result = readline_until(com, "=>")
    if "done" in result:
        log("Success!", print_log)
        log("Environments updated successfully.", print_log)
    else:
        log("Failure!", print_log)
        log("Environments could not be updated.", print_log)
        log("Exiting script...", print_log)
        com.close()
        return

    log("Finished updating images.", print_log)

    # boot to login prompt
    log("Booting kernel...", print_log)
    booted = boot_to_login(com)
    if booted:
        log("Kernel update is complete.", print_log)
    else:
        log("Failure!", print_log)
        log("Failed to boot kernel.", print_log)
        log("Exiting script...", print_log)
        com.close()
        return

    com.close()
    

def get_input_args():
    """
    Parse command line arguments.

    usage: update_kernel.py [-h] [--port PORT] [--boot_image BOOT]
                            [--rootfs_image ROOTFS] [--recovery_image RECOVERY]

    positional arguments:
        none

    optional arguments:
        -h, --help                  show this help message and exit
        --port PORT                 The COM port on which the FTDI serial device is connected.
                                    On Windows machines, this will be the word COM followed by
                                    a port number. By default, this script scans for FTDI
                                    devices and selects one if available.
        --boot_image BOOT           The name of the boot image file to be flashed;
                                    default=core-image-base-ccimx6sbc.boot.vfat
        --rootfs_image ROOTFS       The name of the rootfs image file to be flashed;
                                    default=core-image-base-ccimx6sbc.rootfs.ext4
        --recovery_image RECOVERY   The name of the recovery image file to be flashed;
                                    default=core-image-base-ccimx6sbc.recovery.vfat

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
    parser.add_argument('--boot_image', action="store", type=str, 
                        default='core-image-base-ccimx6sbc.boot.vfat',
                        help='The name of the boot image file to be flashed; ' \
                             'default=core-image-base-ccimx6sbc.boot.vfat')
    parser.add_argument('--rootfs_image', action="store", type=str, 
                        default='core-image-base-ccimx6sbc.rootfs.ext4',
                        help='The name of the rootfs image file to be flashed; ' \
                             'default=core-image-base-ccimx6sbc.rootfs.ext4')
    parser.add_argument('--recovery_image', action="store", type=str, 
                        default='core-image-base-ccimx6sbc.recovery.vfat',
                        help='The name of the recovery image file to be flashed; ' \
                             'default=core-image-base-ccimx6sbc.recovery.vfat')
    return parser.parse_args()

if __name__ == '__main__':
    main()
