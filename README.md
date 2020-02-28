# Command Line tool for updating devices with U-Boot via SD card and serial port

This tool will automatically install uboot images, kernel images, and application images for the device.
This tool is specific to a device and may not be used for other uboot devices.

For any questions, contact the author: steven.lowery@honeywell.com

# Installation

No installation required, aside from Python and the pyserial package.
```
pip install -r requirements.txt
```

# Dependencies

Python 3.x

`pyserial`


# Usage

There are three tools in this package: one for updating the bootloader firmware, another for updating the Yocto kernel firmware, and a third for updating application software.

If the device is brand new out-of-box, an initial bootloader installation requires booting from the SD card.
To boot from the SD card, the programming button must be held while powering on the device.
After programming the initial bootloader, further bootloader updates do not generally require booting from the SD card, though it is always recommended.

It is always recommended to do a hard power-on-reset (POR) between each installation, though it is not required so long as the device did not boot from SD card.

In general, the procedure should be as follows:
1. SD card is inserted
2. Boot from SD card by holding the programming button while powering on.
3. Install the bootloader from SD card using `update_bootloader.py`
4. Power on reset
5. Install the Yocto kernel images using `update_kernel.py`
6. Power on reset
7. Install the application using `update_application.py`

For a device that is already programmed and simply needs updating, the procedure may be as follows:
1. SD card is inserted
2. Power on the device
3. Install the necessary base updates (bootloader or kernel) with `update_bootloader.py` or `update_kernel.py`
4. Install the new application (no POR required) with `update_application.py`

For a device that simply needs an application update from the SD card, the procedure is simple:
1. SD card is inserted
2. Power on the device
3. Update the application with `update_application.py`

### Python

```
pip install -r requirements.txt
```

### Command Line

```
usage: update_bootloader.py [-h] [--port PORT] [--image IMAGE]

optional arguments:
  -h, --help     show this help message and exit
  --port PORT    The COM port on which the FTDI serial device is connected. On
                 Windows machines, this will be the word COM followed by a
                 port number. By default, this script scans for FTDI devices
                 and selects one if available.
  --image IMAGE  The name of the u-boot image file to be flashed;
                 default=u-boot-ccimx6qsbc.imx
```

```
usage: update_kernel.py [-h] [--port PORT] [--boot_image BOOT_IMAGE]
                        [--rootfs_image ROOTFS_IMAGE]
                        [--recovery_image RECOVERY_IMAGE]

optional arguments:
  -h, --help            show this help message and exit
  --port PORT           The COM port on which the FTDI serial device is
                        connected. On Windows machines, this will be the word
                        COM followed by a port number. By default, this script
                        scans for FTDI devices and selects one if available.
  --boot_image BOOT_IMAGE
                        The name of the boot image file to be flashed;
                        default=core-image-base-ccimx6sbc.boot.vfat
  --rootfs_image ROOTFS_IMAGE
                        The name of the rootfs image file to be flashed;
                        default=core-image-base-ccimx6sbc.rootfs.ext4
  --recovery_image RECOVERY_IMAGE
                        The name of the recovery image file to be flashed;
                        default=core-image-base-ccimx6sbc.recovery.vfat
```

```
usage: update_application.py [-h] [--port PORT] [--root_psswd ROOT_PSSWD]
                             serialno

positional arguments:
  serialno              The new serial number to be flashed on the device.

optional arguments:
  -h, --help            show this help message and exit
  --port PORT           The COM port on which the FTDI serial device is
                        connected. On Windows machines, this will be the word
                        COM followed by a port number. By default, this script
                        scans for FTDI devices and selects one if available.
  --root_psswd ROOT_PSSWD
                        The new root password if other than the default.
                        default=Allergen_lock
```