"""
uboot_gui.py
This script creates a GUI for using the three update tools to load new firmware
to the U-Boot device. The GUI uses the tkinter framework. 
"""

import tkinter
import tkinter.scrolledtext as tkst
from tkinter import messagebox
import datetime
import serial
import serial.tools.list_ports
from uboot import log
from update_application import update_application
from update_bootloader import update_bootloader
from update_kernel import update_kernel
import threading

def change_port():
    current_port_entry.configure(state='normal')

def try_port():
    comport = port.get()
    try:
        com = serial.Serial(comport, 115200, timeout=1)
        com.close()
        log("Comport {} is ready to use".format(comport), print_log=False, widget=text)
        messagebox.showinfo("Success!", "Comport {} is ready to use".format(comport))
        current_port_entry.configure(state='disabled')
    except serial.SerialException:
        log("Could not access comport {}".format(comport), print_log=False, widget=text)
        messagebox.showwarning("Warning!", "Could not access comport {}".format(comport))

def auto_detect():
    auto_detect_button.configure(bg='SystemButtonFace')
    port_label.configure(state='normal')
    current_port_entry.configure(state='normal')
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
    usb_serial_ports = []
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
        log("Auto-detect found multiple FTDI comports: {}".format(usb_serial_ports), print_log=False, widget=text)
        messagebox.showinfo("Multiple devices found", 
                            "Multiple FTDI comports were found on the system. " \
                            "The first device found was automatically selected. If you want " \
                            "to use another device, please click the Change Port button and " \
                            "manually enter the comport you would like to use in the " \
                            "entry box, then click the Try Port button. ")
    else:
        port_val = usb_serial_ports[0]
        log("Auto-detect found FTDI comport: {}".format(usb_serial_ports[0]), print_log=False, widget=text)
    
    current_port_entry.configure(state='normal')
    current_port_entry.delete(0, 20)
    if port_val != "":
        current_port_entry.insert(0, port_val)
        current_port_entry.configure(state='disabled')
    try_port()

def program_bootloader():
    log("Running bootloader programming tool...", print_log=False, widget=text)
    update_bootloader(port.get())

def program_kernel():
    log("Running kernel programming tool...", print_log=False, widget=text)
    update_kernel(port.get())

def program_application():
    log("Running application programming tool...", print_log=False, widget=text)
    comport = port.get()
    sn = serialno.get()
    update_app_thread = threading.Thread(target=update_application, args=(comport, sn), kwargs={"log_widget": text})
    update_app_thread.start()

def update_serialno():
    num = unit.get()
    sn = 'BIO-' + build.get() + '-' + f'{num:08}'
    sn_entry_box.configure(state='normal')
    sn_entry_box.delete(0, 20)
    sn_entry_box.insert(0, sn)
    sn_entry_box.configure(state='disabled')

# define the GUI window
window = tkinter.Tk()
window.title("title")

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
#window.mainloop()
while True:
    window.update_idletasks()
    window.update()
