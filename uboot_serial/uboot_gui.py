"""
uboot_gui.py
This script creates a GUI for using the three update tools to load new firmware
to the U-Boot device. The GUI uses the tkinter framework.
"""

import os
import tkinter
import tkinter.scrolledtext as tkst
from tkinter import messagebox
import time
import threading
import serial
import serial.tools.list_ports
from uboot import log
from update_application import update_application
from update_bootloader import update_bootloader
from update_kernel import update_kernel


# class definitions
class ApplicationUpdater(threading.Thread):
    """
    A subclass of Thread, overriding the run() method.
    Allows for handling exceptions and showing a resulting message box.
    """
    def __init__(self, comport, serial_num, log_widget):
        threading.Thread.__init__(self)
        self.port = comport
        self.serialno = serial_num
        self.log_widget = log_widget

    def run(self):
        try:
            update_application(self.port, self.serialno, log_widget=self.log_widget)
            messagebox.showinfo("Success!", "Application update finished successfully.")
        except (serial.SerialException, TypeError, ValueError, RuntimeError):
            messagebox.showerror("Error!", "Application update exited with errors.")

class KernelUpdater(threading.Thread):
    """
    A subclass of Thread, overriding the run() method.
    Allows for handling exceptions and showing a resulting message box.
    """
    def __init__(self, comport, log_widget):
        threading.Thread.__init__(self)
        self.port = comport
        self.log_widget = log_widget
        self.firmware = {"boot_image": 'core-image-base-ccimx6sbc.boot.vfat',
                         "rootfs_image": 'core-image-base-ccimx6sbc.rootfs.ext4',
                         "recovery_image": 'core-image-base-ccimx6sbc.recovery.vfat'}

    def run(self):
        try:
            update_kernel(self.port, self.firmware, log_widget=self.log_widget)
            messagebox.showinfo("Success!", "Kernel update finished successfully.")
        except (serial.SerialException, TypeError, ValueError, RuntimeError):
            messagebox.showerror("Error!", "Kernel update exited with errors.")

class BootloaderUpdater(threading.Thread):
    """
    A subclass of Thread, overriding the run() method.
    Allows for handling exceptions and showing a resulting message box.
    """
    def __init__(self, comport, log_widget):
        threading.Thread.__init__(self)
        self.port = comport
        self.log_widget = log_widget
        self.image = 'u-boot-ccimx6qsbc.imx'

    def run(self):
        try:
            update_bootloader(self.port, self.image, log_widget=self.log_widget)
            messagebox.showinfo("Success!", "Bootloader update finished successfully.")
        except (serial.SerialException, TypeError, ValueError, RuntimeError):
            messagebox.showerror("Error!", "Bootloader update exited with errors.")

# general functions
def thread_monitor():
    """
    Checks the current threads and decides whether or not to enable GUI inputs.
    If any updater is in progress, the GUI inputs are disabled.
    """
    threads = [thread.name for thread in threading.enumerate()]
    terms = ['thread-update-app', 'thread-update-kernel', 'thread-update-bootloader']
    if any(thread in threads for thread in terms):
        disable_inputs()
    else:
        enable_inputs()
    WINDOW.after(2000, thread_monitor)

def disable_inputs():
    """
    Disables GUI inputs while crucial threads are running.
    """
    PORT_LABEL.configure(state='disabled')
    FTDI_LABEL.configure(state='disabled')
    TRY_PORT_BUTTON.configure(state='disabled')
    CHANGE_PORT_BUTTON.configure(state='disabled')
    PROG_BOOTLOADER_BTN.configure(state='disabled')
    PROG_KERNEL_BTN.configure(state='disabled')
    PROG_APP_BTN.configure(state='disabled')
    BUILD_LABEL.configure(state='disabled')
    UNIT_LABEL.configure(state='disabled')
    SN_LABEL.configure(state='disabled')
    BUILD_SPINBOX.configure(state='disabled')
    UNIT_SPINBOX.configure(state='disabled')
    SN_UPDATE_BTN.configure(state='disabled')
    AUTO_DETECT_BUTTON.configure(state='disabled')
    GENERATE_QR_BTN.configure(state='disabled')
    PRINT_QR_BTN.configure(state='disabled')

def enable_inputs():
    """
    Enables all GUI inputs.
    """
    PORT_LABEL.configure(state='normal')
    FTDI_LABEL.configure(state='normal')
    TRY_PORT_BUTTON.configure(state='normal')
    CHANGE_PORT_BUTTON.configure(state='normal')
    PROG_BOOTLOADER_BTN.configure(state='normal')
    PROG_KERNEL_BTN.configure(state='normal')
    PROG_APP_BTN.configure(state='normal')
    BUILD_LABEL.configure(state='normal')
    UNIT_LABEL.configure(state='normal')
    SN_LABEL.configure(state='normal')
    BUILD_SPINBOX.configure(state='normal')
    UNIT_SPINBOX.configure(state='normal')
    SN_UPDATE_BTN.configure(state='normal')
    AUTO_DETECT_BUTTON.configure(state='normal')
    GENERATE_QR_BTN.configure(state='normal')
    PRINT_QR_BTN.configure(state='normal')

# button click functions
def change_port():
    """
    GUI Button: Change Port

    Enables the entry box for manually entering the COM port.
    """
    CURRENT_PORT_ENTRY.configure(state='normal')
    FTDI_LABEL.configure(text="")

def try_port():
    """
    GUI Button: Try Port

    Checks to see if the currently selected port is accessible.
    Upon success, a message box pops up and the entry box is disabled for further input.
    Upon failure, a warning box pops up and the entry box is enabled for new input.
    """
    comport = PORT.get()
    try:
        com = serial.Serial(comport, 115200, timeout=1)
        if com.name in [port.device for port in serial.tools.list_ports.grep("0403")]:
            FTDI_LABEL.configure(text="(FTDI Device detected)")
            log("Comport {} is an FTDI device".format(comport), print_log=False,
                widget=LOGWINDOW)
        else:
            FTDI_LABEL.configure(text="(Not an FTDI device)")
            log("Comport {} is not an FTDI device".format(comport), print_log=False,
                widget=LOGWINDOW)
        com.close()
        log("Comport {} is ready to use".format(comport), print_log=False, widget=LOGWINDOW)
        messagebox.showinfo("Success!", "Comport {} is ready to use".format(comport))
        CURRENT_PORT_ENTRY.configure(state='disabled')
    except serial.SerialException:
        log("Could not access comport {}".format(comport), print_log=False, widget=LOGWINDOW)
        FTDI_LABEL.configure(text="(unavailable)")
        messagebox.showwarning("Warning!", "Could not access comport {}".format(comport))

def auto_detect():
    """
    GUI Button: Auto Detect

    Checks system serial ports for all FTDI devices.
    This button must be clicked first upon using the GUI.
    If multiple FTDI devices are found, the first is selected and an info box pops up.
    If no FTDI devices are found, a warning box pops up and the user may manually
    enter a selected COM port.
    """
    AUTO_DETECT_BUTTON.configure(bg='SystemButtonFace')
    CURRENT_PORT_ENTRY.configure(state='normal')
    enable_inputs()
    usb_serial_ports = []
    # search for FTDI devices by vendor ID
    for comport in serial.tools.list_ports.grep("0403"):
        usb_serial_ports.append(comport.device)
    if usb_serial_ports == []:
        # no FTDI devices found
        port_val = ""
        log("Auto-detect found no FTDI comports", print_log=False, widget=LOGWINDOW)
        messagebox.showwarning("Warning!", "No FTDI comports were found on the system. " \
                               "Please manually enter the comport you would like to use " \
                               "in the entry box or plug in an FTDI device and try again. ")
    elif len(usb_serial_ports) > 1:
        # found multiple FTDI devices
        port_val = usb_serial_ports[0]
        log("Auto-detect found multiple FTDI comports: {}".format(usb_serial_ports),
            print_log=False, widget=LOGWINDOW)
        messagebox.showinfo("Multiple devices found",
                            "Multiple FTDI comports were found on the system. " \
                            "The first device found was automatically selected. If you " \
                            "want to use another device, please click the Change Port " \
                            "button and manually enter the comport you would like to use " \
                            "in the entry box, then click the Try Port button. ")
    else:
        # found only one FTDI device
        port_val = usb_serial_ports[0]
        log("Auto-detect found FTDI comport: {}".format(usb_serial_ports[0]),
            print_log=False, widget=LOGWINDOW)
    CURRENT_PORT_ENTRY.configure(state='normal')
    CURRENT_PORT_ENTRY.delete(0, 20)
    if port_val != "":
        CURRENT_PORT_ENTRY.insert(0, port_val)
        CURRENT_PORT_ENTRY.configure(state='disabled')
    try_port()
    # since this button is clicked at GUI start, initiate the thread monitor now
    WINDOW.after(1000, thread_monitor)

def program_bootloader():
    """
    GUI Button: Program Bootloader

    Instantiates a thread object for calling the bootloader update tool.
    """
    comport = PORT.get()
    if messagebox.askyesno("Progam Bootloader?", "Do you want to program the bootloader?"):
        messagebox.showinfo("Boot From SD Card", "To program the bootloader from the " \
                            "SD card, you must boot from the SD card by holding the " \
                            "programming button while turning on the unit. Please do " \
                            "so now, then click OK.")
        log("Running bootloader programming tool...", print_log=False, widget=LOGWINDOW)
        time.sleep(5)
        update_btl_thread = BootloaderUpdater(comport, LOGWINDOW)
        update_btl_thread.name = 'thread-update-bootloader'
        update_btl_thread.start()

def program_kernel():
    """
    GUI Button: Program Kernel

    Instantiates a thread object for calling the kernel update tool.
    """
    comport = PORT.get()
    if messagebox.askyesno("Progam Kernel?", "Do you want to program the kernel?"):
        messagebox.showinfo("Turn OFF Device", "It is recommended to start the kernel " \
                            "update procedure from an " \
                            "OFF state. Please power the device OFF then click OK.")
        log("Running kernel programming tool...", print_log=False, widget=LOGWINDOW)
        update_os_thread = KernelUpdater(comport, LOGWINDOW)
        update_os_thread.name = 'thread-update-kernel'
        update_os_thread.start()

def program_application():
    """
    GUI Button: Program Application

    Instantiates a thread object for calling the application update tool.
    """
    comport = PORT.get()
    update_serialno()
    serial_num = SERIALNO.get()
    if messagebox.askyesno("Progam application?", "Do you want to program the application " \
                            "software with serial number {}?".format(serial_num)):
        log("Running application programming tool...", print_log=False, widget=LOGWINDOW)
        update_app_thread = ApplicationUpdater(comport, serial_num, LOGWINDOW)
        update_app_thread.name = 'thread-update-app'
        update_app_thread.start()

def update_serialno():
    """
    GUI Button: Update Serial Number

    Updates the selected serial number entry box with the current selections.
    """
    num = UNIT.get()
    serial_num = 'BIO-' + BUILD.get() + '-' + f'{num:08}'
    SN_ENTRY_BOX.configure(state='normal')
    SN_ENTRY_BOX.delete(0, 20)
    SN_ENTRY_BOX.insert(0, serial_num)
    SN_ENTRY_BOX.configure(state='disabled')

def generate_qrcode():
    """
    GUI Button: Generate QR Code

    Generates a QR code of the current serial number and saves as PNG.
    """
    try:
        import qrcode
    except ImportError:
        messagebox.showerror("Module ImportError", "The qrcode module is not installed.")
        return
    update_serialno()
    qrcode_text = "Allergen_"+SERIALNO.get()
    if not os.path.exists("./QR_codes"):
        os.mkdir("./QR_codes")
    path = os.getcwd() + "\\QR_codes\\{}.png".format(qrcode_text)
    qrcode.make(qrcode_text, box_size=8, border=1).crop((7, 7, 209, 209)).save(path)
    log("QR code saved to {}".format(path), print_log=False, widget=LOGWINDOW)
    messagebox.showinfo("File Saved", "QR code has been saved as {}".format(path))

def print_qr_label():
    """
    GUI Button: Print QR Label

    Prints a QR code label for the current serial number 
    to a connected Brother QL-500 label printer.
    Requires brother_ql module and libusb0.dll installed on the system.
    """
    # check if the Brother Python module is installed
    try:
        import brother_ql
    except ImportError:
        messagebox.showerror("Module ImportError", "The brother_ql module is not installed.")
        return
    
    # Check if the PyUSB module is installed
    try:
        import usb.core
        import usb.libloader
    except ImportError:
        messagebox.showerror("Module ImportError", "The pyusb module is not installed.")
        return
    
    # Check if the libusb0 library is installed and discoverable
    lib = usb.libloader.locate_library(('usb', 'libusb0'))
    if not lib:
        messagebox.showerror("USB Library Not Found", "The shared library libusb0.dll " \
                             "could not be found in PATH. Make sure that libusb0.dll is " \
                             "installed and discoverable in the PATH environment variable.")
        return
    
    # Try to load the libusb0 library
    try:
        import ctypes
        ctypes.CDLL(lib)
        loaded_lib = usb.libloader.load_library(lib)
        if not loaded_lib:
            messagebox.showerror("Library Load Failed",
                                 "The library {} could not be loaded by the " \
                                 "libloader in PyUSB.".format(lib))
            return
    except OSError:
        messagebox.showerror("Library Load Failed",
                             "The library {} could not be loaded. The library may not be " \
                             "the proper type. This application requires a 32-bit library " \
                             "libusb0.dll discoverable in PATH.".format(lib))
        return
    
    # Try to setup the library with USB functions
    try:
        from usb.backend.libusb0 import _setup_prototypes as setup_prototypes
        setup_prototypes(loaded_lib)
        loaded_lib.usb_init()
    except:
        messagebox.showerror("Library Init Failed",
                             "The library {} could not be Initialized. ".format(loaded_lib))

    # Check if the PyUSB API can access the libusb0 backend
    import usb.backend.libusb0 as libusb0
    if not libusb0.get_backend():
        messagebox.showerror("Cannot Access Backend", 
                             "The libusb0 backend is not accessible by PyUSB.")
        return
    
    try:
        if not usb.core.find(idVendor=0x04f9):
            messagebox.showerror("Cannot Find Device", 
                                 "The Brother QL-500 printer device could not be found.")
            return
    except usb.core.NoBackendError:
        messagebox.showerror("Could Not Find Backend", 
                                 "The backend - PyUSB (libusb0.dll) - was not found.")
        return
    
    update_serialno()
    qrcode_text = "Allergen_"+SERIALNO.get()
    path = os.getcwd() + "\\QR_codes\\{}.png".format(qrcode_text)
    if not os.path.exists(path):
        generate_qrcode()
    from brother_ql.conversion import convert
    from brother_ql.backends.helpers import send
    from brother_ql.raster import BrotherQLRaster
    qlr = BrotherQLRaster('QL-500')
    instructions = convert(qlr=qlr, images=[path], label='23x23')
    send(instructions=instructions, printer_identifier='usb://0x04f9:0x2015',
         backend_identifier='pyusb', blocking=True)
    send(instructions=instructions, printer_identifier='usb://0x04f9:0x2015',
         backend_identifier='pyusb', blocking=True)
    log("Label print completed.", print_log=False, widget=LOGWINDOW)
    messagebox.showinfo("Finished", "Label {} printing has completed".format(qrcode_text))

# define the GUI window
WINDOW = tkinter.Tk()
WINDOW.title("Allergen Sensor Serial Programming Tool")

# define the frames in the window
OUTPUTFRAME = tkinter.Frame(WINDOW, height=600, width=800)
INPUTFRAME = tkinter.Frame(WINDOW, height=600, width=500)
OUTPUTFRAME.pack(side=tkinter.LEFT)
INPUTFRAME.pack(side=tkinter.RIGHT)
INPUTFRAME.pack_propagate(0)
INPUTFRAME.grid_propagate(0)

# define the output window text box
LOGWINDOW = tkst.ScrolledText(OUTPUTFRAME, height=40, width=100)
LOGWINDOW.pack()
LOGWINDOW.configure(state='disabled')

# define the inputs
# port selection labels and change-port/try-port buttons
PORT = tkinter.StringVar()
PORT_LABEL = tkinter.Label(INPUTFRAME, text="Port: ", state='disabled')
PORT_LABEL.grid(row=0, column=0, padx=5, pady=5)
CURRENT_PORT_ENTRY = tkinter.Entry(INPUTFRAME, textvariable=PORT, state='disabled')
CURRENT_PORT_ENTRY.grid(row=0, column=1, padx=5, pady=5)
FTDI_LABEL = tkinter.Label(INPUTFRAME, text="", state='disabled')
FTDI_LABEL.grid(row=1, column=1, padx=5, pady=0)
TRY_PORT_BUTTON = tkinter.Button(INPUTFRAME, text="Try Port", command=try_port,
                                 state='disabled')
TRY_PORT_BUTTON.grid(row=0, column=2, padx=5, pady=5)
CHANGE_PORT_BUTTON = tkinter.Button(INPUTFRAME, text="Change Port", command=change_port,
                                    state='disabled')
CHANGE_PORT_BUTTON.grid(row=0, column=3, padx=5, pady=5)
AUTO_DETECT_BUTTON = tkinter.Button(INPUTFRAME, text="Auto Detect", command=auto_detect,
                                    bg='green')
AUTO_DETECT_BUTTON.grid(row=1, column=3, padx=5, pady=5)

# programming buttons
PROG_BOOTLOADER_BTN = tkinter.Button(INPUTFRAME, text="Program Bootloader", width=30,
                                     command=program_bootloader, state='disabled')
PROG_BOOTLOADER_BTN.grid(row=2, column=0, rowspan=2, columnspan=2, padx=5, pady=20)
PROG_KERNEL_BTN = tkinter.Button(INPUTFRAME, text="Program Kernel", width=30,
                                 command=program_kernel, state='disabled')
PROG_KERNEL_BTN.grid(row=4, column=0, rowspan=2, columnspan=2, padx=5, pady=20)
PROG_APP_BTN = tkinter.Button(INPUTFRAME, text="Program Application", width=30,
                              command=program_application, state='disabled')
PROG_APP_BTN.grid(row=6, column=0, rowspan=2, columnspan=2, padx=5, pady=20)

# serial number entries and spinbox
BUILD_LABEL = tkinter.Label(INPUTFRAME, text="Build: ", state='disabled')
BUILD_LABEL.grid(row=8, column=0, padx=5, pady=20)
UNIT_LABEL = tkinter.Label(INPUTFRAME, text="Unit No.: ", state='disabled')
UNIT_LABEL.grid(row=10, column=0, padx=5, pady=20)
SN_LABEL = tkinter.Label(INPUTFRAME, text="SerialNo: ", state='disabled')
SN_LABEL.grid(row=12, column=0, padx=5, pady=20)
BUILD = tkinter.StringVar()
BUILD_SPINBOX = tkinter.Spinbox(INPUTFRAME,
                                values=('CV1', 'CV2', 'DV1', 'DV2', 'PV1', 'PV2', 'XXX'),
                                textvariable=BUILD, state='disabled')
BUILD_SPINBOX.grid(row=8, column=1, padx=5, pady=20)
UNIT = tkinter.IntVar()
UNIT_SPINBOX = tkinter.Spinbox(INPUTFRAME, from_=0, to=99999999, textvariable=UNIT,
                               state='disabled')
UNIT_SPINBOX.grid(row=10, column=1, padx=5, pady=20)
SERIALNO = tkinter.StringVar()
SN_ENTRY_BOX = tkinter.Entry(INPUTFRAME, textvariable=SERIALNO, state='disabled')
SN_ENTRY_BOX.grid(row=12, column=1, padx=5, pady=20)
SN_ENTRY_BOX.delete(0)
SN_ENTRY_BOX.configure(state='disabled')
update_serialno()
SN_UPDATE_BTN = tkinter.Button(INPUTFRAME, text="Update Serial No.",
                               command=update_serialno, state='disabled')
SN_UPDATE_BTN.grid(row=12, column=2, padx=5, pady=20)

# QR code generator and label print buttons
GENERATE_QR_BTN = tkinter.Button(INPUTFRAME, text="Generate QR Code",
                                 command=generate_qrcode,
                                 state='disabled')
GENERATE_QR_BTN.grid(row=14, column=2, padx=5, pady=20)
PRINT_QR_BTN = tkinter.Button(INPUTFRAME, text="Print QR Label",
                                 command=print_qr_label,
                                 state='disabled')
PRINT_QR_BTN.grid(row=16, column=2, padx=5, pady=20)

# main GUI loop
log("Welcome to the U-Boot device update tool!", print_log=False, widget=LOGWINDOW)
log("Please insert an SD card into a device and connect to the serial port with an FTDI " \
    "serial converter.", print_log=False, widget=LOGWINDOW)
log("Click Auto Detect to find serial ports and begin...", print_log=False, widget=LOGWINDOW)
WINDOW.mainloop()
