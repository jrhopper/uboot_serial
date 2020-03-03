"""
uboot_gui.py
This script creates a GUI for using the three update tools to load new firmware
to the U-Boot device. The GUI uses the tkinter framework. 
"""

import tkinter
import tkinter.scrolledtext as tkst
from tkinter import messagebox
import time
import datetime
import serial
import serial.tools.list_ports
from uboot import log
from update_application import update_application
from update_bootloader import update_bootloader
from update_kernel import update_kernel
import threading

# class definitions
class application_updater(threading.Thread):
    """
    A subclass of Thread, overriding the run() method.
    Allows for handling exceptions and showing a resulting message box.
    """
    def __init__(self, port, serialno, log_widget):
        threading.Thread.__init__(self)
        self.port = port
        self.serialno = serialno
        self.log_widget = log_widget

    def run(self):
        try:
            update_application(self.port, self.serialno, log_widget=self.log_widget)
            messagebox.showinfo("Success!", "Application update finished successfully.")
        except Exception:
            messagebox.showerror("Error!", "Application update exited with errors.")

class kernel_updater(threading.Thread):
    """
    A subclass of Thread, overriding the run() method.
    Allows for handling exceptions and showing a resulting message box.
    """
    def __init__(self, port, log_widget):
        threading.Thread.__init__(self)
        self.port = port
        self.log_widget = log_widget
        self.firmware = {"boot_image": 'core-image-base-ccimx6sbc.boot.vfat',
                         "rootfs_image": 'core-image-base-ccimx6sbc.rootfs.ext4',
                         "recovery_image": 'core-image-base-ccimx6sbc.recovery.vfat'}

    def run(self):
        try:
            update_kernel(self.port, self.firmware, log_widget=self.log_widget)
            messagebox.showinfo("Success!", "Kernel update finished successfully.")
        except Exception:
            messagebox.showerror("Error!", "Kernel update exited with errors.")

class bootloader_updater(threading.Thread):
    """
    A subclass of Thread, overriding the run() method.
    Allows for handling exceptions and showing a resulting message box.
    """
    def __init__(self, port, log_widget):
        threading.Thread.__init__(self)
        self.port = port
        self.log_widget = log_widget
        self.image = 'u-boot-ccimx6qsbc.imx'

    def run(self):
        try:
            update_bootloader(self.port, self.image, log_widget=self.log_widget)
            messagebox.showinfo("Success!", "Bootloader update finished successfully.")
        except Exception:
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
    window.after(2000, thread_monitor)

def disable_inputs():
    """
    Disables GUI inputs while crucial threads are running. 
    """
    port_label.configure(state='disabled')
    ftdi_label.configure(state='disabled')
    try_port_button.configure(state='disabled')
    change_port_button.configure(state='disabled')
    prog_bootloader_btn.configure(state='disabled')
    prog_kernel_btn.configure(state='disabled')
    prog_app_btn.configure(state='disabled')
    build_label.configure(state='disabled')
    unit_label.configure(state='disabled')
    sn_label.configure(state='disabled')
    build_spinbox.configure(state='disabled')
    unit_spinbox.configure(state='disabled')
    sn_update_btn.configure(state='disabled')
    auto_detect_button.configure(state='disabled')

def enable_inputs():
    """
    Enables all GUI inputs. 
    """
    port_label.configure(state='normal')
    ftdi_label.configure(state='normal')
    try_port_button.configure(state='normal')
    change_port_button.configure(state='normal')
    prog_bootloader_btn.configure(state='normal')
    prog_kernel_btn.configure(state='normal')
    prog_app_btn.configure(state='normal')
    build_label.configure(state='normal')
    unit_label.configure(state='normal')
    sn_label.configure(state='normal')
    build_spinbox.configure(state='normal')
    unit_spinbox.configure(state='normal')
    sn_update_btn.configure(state='normal')
    auto_detect_button.configure(state='normal')

# button click functions
def change_port():
    """
    GUI Button: Change Port

    Enables the entry box for manually entering the COM port.
    """
    current_port_entry.configure(state='normal')
    ftdi_label.configure(text="")

def try_port():
    """
    GUI Button: Try Port

    Checks to see if the currently selected port is accessible.
    Upon success, a message box pops up and the entry box is disabled for further input.
    Upon failure, a warning box pops up and the entry box is enabled for new input. 
    """
    comport = port.get()
    try:
        com = serial.Serial(comport, 115200, timeout=1)
        if com.name in [port.device for port in serial.tools.list_ports.grep("0403")]:
            ftdi_label.configure(text="(FTDI Device detected)")
            log("Comport {} is an FTDI device".format(comport), print_log=False, widget=text)
        else:
            ftdi_label.configure(text="(Not an FTDI device)")
            log("Comport {} is not an FTDI device".format(comport), print_log=False, widget=text)
        com.close()
        log("Comport {} is ready to use".format(comport), print_log=False, widget=text)
        messagebox.showinfo("Success!", "Comport {} is ready to use".format(comport))
        current_port_entry.configure(state='disabled')
    except serial.SerialException:
        log("Could not access comport {}".format(comport), print_log=False, widget=text)
        ftdi_label.configure(text="(unavailable)")
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
    auto_detect_button.configure(bg='SystemButtonFace')
    current_port_entry.configure(state='normal')
    enable_inputs()
    usb_serial_ports = []
    # search for FTDI devices by vendor ID
    for port in serial.tools.list_ports.grep("0403"):
        usb_serial_ports.append(port.device)
    if usb_serial_ports == []:
        # no FTDI devices found
        port_val = ""
        log("Auto-detect found no FTDI comports", print_log=False, widget=text)
        messagebox.showwarning("Warning!", "No FTDI comports were found on the system. " \
                               "Please manually enter the comport you would like to use " \
                               "in the entry box or plug in an FTDI device and try again. ")
    elif len(usb_serial_ports) > 1:
        # found multiple FTDI devices
        port_val = usb_serial_ports[0]
        log("Auto-detect found multiple FTDI comports: {}".format(usb_serial_ports), 
            print_log=False, widget=text)
        messagebox.showinfo("Multiple devices found", 
                            "Multiple FTDI comports were found on the system. " \
                            "The first device found was automatically selected. If you " \
                            "want to use another device, please click the Change Port " \
                            "button and manually enter the comport you would like to use " \
                            "in the entry box, then click the Try Port button. ")
    else:
        # found only one FTDI device
        port_val = usb_serial_ports[0]
        log("Auto-detect found FTDI comport: {}".format(usb_serial_ports[0]), print_log=False, widget=text)
    current_port_entry.configure(state='normal')
    current_port_entry.delete(0, 20)
    if port_val != "":
        current_port_entry.insert(0, port_val)
        current_port_entry.configure(state='disabled')
    try_port()
    # since this button is clicked at GUI start, initiate the thread monitor now
    window.after(1000, thread_monitor)

def program_bootloader():
    """
    GUI Button: Program Bootloader

    Instantiates a thread object for calling the bootloader update tool.
    """
    comport = port.get()
    if messagebox.askyesno("Progam Bootloader?", "Do you want to program the bootloader?"):
        messagebox.showinfo("Boot From SD Card", "To program the bootloader from the SD card, " \
                            "you must boot from the SD card by holding the programming " \
                            "button while turning on the unit. Please do so now, " \
                            "then click OK.")
        log("Running bootloader programming tool...", print_log=False, widget=text)
        time.sleep(5)
        update_btl_thread = bootloader_updater(comport, text)
        update_btl_thread.name = 'thread-update-bootloader'
        update_btl_thread.start()

def program_kernel():
    """
    GUI Button: Program Kernel

    Instantiates a thread object for calling the kernel update tool.
    """
    comport = port.get()
    if messagebox.askyesno("Progam Kernel?", "Do you want to program the kernel?"):
        messagebox.showinfo("Turn OFF Device", "It is recommended to start the kernel update procedure from an " \
                            "OFF state. Please power the device OFF then click OK.")
        log("Running kernel programming tool...", print_log=False, widget=text)
        update_os_thread = kernel_updater(comport, text)
        update_os_thread.name = 'thread-update-kernel'
        update_os_thread.start()

def program_application():
    """
    GUI Button: Program Application

    Instantiates a thread object for calling the application update tool.
    """
    comport = port.get()
    update_serialno()
    sn = serialno.get()
    if messagebox.askyesno("Progam application?", "Do you want to program the application software with serial number {}?".format(sn)):
        log("Running application programming tool...", print_log=False, widget=text)
        update_app_thread = application_updater(comport, sn, text)
        update_app_thread.name = 'thread-update-app'
        update_app_thread.start()

def update_serialno():
    """
    GUI Button: Update Serial Number

    Updates the selected serial number entry box with the current selections. 
    """
    num = unit.get()
    sn = 'BIO-' + build.get() + '-' + f'{num:08}'
    sn_entry_box.configure(state='normal')
    sn_entry_box.delete(0, 20)
    sn_entry_box.insert(0, sn)
    sn_entry_box.configure(state='disabled')

# define the GUI window
window = tkinter.Tk()
window.title("Allergen Sensor Serial Programming Tool")

# define the frames in the window
outputFrame = tkinter.Frame(window, height=600, width=800)
inputFrame = tkinter.Frame(window, height=600, width=500)
outputFrame.pack(side=tkinter.LEFT)
inputFrame.pack(side=tkinter.RIGHT)
inputFrame.pack_propagate(0)
inputFrame.grid_propagate(0)

# define the output window text box
text = tkst.ScrolledText(outputFrame, height=40, width=100)
text.pack()
text.configure(state='disabled')

# define the inputs
# port selection labels and change-port/try-port buttons
port = tkinter.StringVar()
port_label = tkinter.Label(inputFrame, text="Port: ", state='disabled')
port_label.grid(row=0, column=0, padx=5, pady=5)
current_port_entry = tkinter.Entry(inputFrame, textvariable=port, state='disabled')
current_port_entry.grid(row=0, column=1, padx=5, pady=5)
ftdi_label = tkinter.Label(inputFrame, text="", state='disabled')
ftdi_label.grid(row=1, column=1, padx=5, pady=0)
try_port_button = tkinter.Button(inputFrame, text="Try Port", command=try_port, state='disabled')
try_port_button.grid(row=0, column=2, padx=5, pady=5)
change_port_button = tkinter.Button(inputFrame, text="Change Port", command=change_port, state='disabled')
change_port_button.grid(row=0, column=3, padx=5, pady=5)
auto_detect_button = tkinter.Button(inputFrame, text="Auto Detect", command=auto_detect, bg='green')
auto_detect_button.grid(row=1, column=3, padx=5, pady=5)

# programming buttons
prog_bootloader_btn = tkinter.Button(inputFrame, text="Program Bootloader", width=30, command=program_bootloader, state='disabled')
prog_bootloader_btn.grid(row=2, column=0, rowspan=2, columnspan=2, padx=5, pady=20)
prog_kernel_btn = tkinter.Button(inputFrame, text="Program Kernel", width=30, command=program_kernel, state='disabled')
prog_kernel_btn.grid(row=4, column=0, rowspan=2, columnspan=2, padx=5, pady=20)
prog_app_btn = tkinter.Button(inputFrame, text="Program Application", width=30, command=program_application, state='disabled')
prog_app_btn.grid(row=6, column=0, rowspan=2, columnspan=2, padx=5, pady=20)

# serial number entries and spinbox
build_label = tkinter.Label(inputFrame, text="Build: ", state='disabled')
build_label.grid(row=8, column=0, padx=5, pady=20)
unit_label = tkinter.Label(inputFrame, text="Unit No.: ", state='disabled')
unit_label.grid(row=10, column=0, padx=5, pady=20)
sn_label = tkinter.Label(inputFrame, text="SerialNo: ", state='disabled')
sn_label.grid(row=12, column=0, padx=5, pady=20)
build = tkinter.StringVar()
build_spinbox = tkinter.Spinbox(inputFrame, values=('CV1', 'CV2', 'DV1', 'DV2', 'PV1', 'PV2', 'XXX'), textvariable=build, state='disabled')
build_spinbox.grid(row=8, column=1, padx=5, pady=20)
unit = tkinter.IntVar()
unit_spinbox = tkinter.Spinbox(inputFrame, from_=0, to=99999999, textvariable=unit, state='disabled')
unit_spinbox.grid(row=10, column=1, padx=5, pady=20)
serialno = tkinter.StringVar()
sn_entry_box = tkinter.Entry(inputFrame, textvariable=serialno, state='disabled')
sn_entry_box.grid(row=12, column=1, padx=5, pady=20)
sn_entry_box.delete(0)
sn_entry_box.configure(state='disabled')
update_serialno()
sn_update_btn = tkinter.Button(inputFrame, text="Update Serial No.", command=update_serialno, state='disabled')
sn_update_btn.grid(row=12, column=2, padx=5, pady=20)

# main GUI loop
log("Welcome to the U-Boot device update tool!", print_log=False, widget=text)
log("Please insert an SD card into a device and connect to the serial port with an FTDI serial converter.", print_log=False, widget=text)
log("Click Auto Detect to find serial ports and begin...", print_log=False, widget=text)
window.mainloop()
