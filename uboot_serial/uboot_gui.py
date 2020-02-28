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

def log(text, print_log=False, widget=None):
    timestamp = datetime.datetime.now().strftime("%b-%d-%Y-%H-%M-%S").upper()
    log_data = "[{}]    ".format(timestamp) + text
    if print_log:
        print(log_data)
    if widget is not None:
        widget.configure(state='normal')
        widget.insert(tkinter.INSERT, log_data + '\n')
        widget.configure(state='disabled')
        widget.yview_moveto(1)    

def change_port():
    log("change_port_button clicked", print_log=True, widget=text)

def try_port():
    log("try_port_button clicked", print_log=True, widget=text)

def refreshPorts():
    usb_serial_ports = []
    for port in serial.tools.list_ports.grep("0403"):
        usb_serial_ports.append(port.device)
    if usb_serial_ports == []:
        # no devices found
        messagebox.askquestion("Warning!", "No FTDI comports were found on the system. Please select the comport you would like to use.")
    if len(usb_serial_ports) > 1:
        # found multiple devices
        pass
    ftdi_port = usb_serial_ports[0]
    return ftdi_port

def program_bootloader():
    log("program bootloader button clicked", print_log=True, widget=text)

def program_kernel():
    log("program kernel button clicked", print_log=True, widget=text)

def program_application():
    log("program application button clicked", print_log=True, widget=text)

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
port = refreshPorts()
port_label = tkinter.Label(inputFrame, text="Port: ")
port_label.grid(row=0, column=0, padx=5, pady=5)
current_port_label = tkinter.Label(inputFrame, text=port)
current_port_label.grid(row=0, column=1, padx=5, pady=5)
try_port_button = tkinter.Button(inputFrame, text="Try Port", command=try_port)
try_port_button.grid(row=0, column=2, padx=5, pady=5)
change_port_button = tkinter.Button(inputFrame, text="Change Port", command=change_port)
change_port_button.grid(row=0, column=3, padx=5, pady=5)

# programming buttons
prog_bootloader_btn = tkinter.Button(inputFrame, text="Program Bootloader", width=30, command=program_bootloader)
prog_bootloader_btn.grid(row=2, column=0, rowspan=2, columnspan=2, padx=5, pady=20)
prog_kernel_btn = tkinter.Button(inputFrame, text="Program Kernel", width=30, command=program_kernel)
prog_kernel_btn.grid(row=4, column=0, rowspan=2, columnspan=2, padx=5, pady=20)
prog_app_btn = tkinter.Button(inputFrame, text="Program Application", width=30, command=program_application)
prog_app_btn.grid(row=6, column=0, rowspan=2, columnspan=2, padx=5, pady=20)

# serial number entries and spinbox
build_label = tkinter.Label(inputFrame, text="Build: ")
build_label.grid(row=8, column=0, padx=5, pady=20)
unit_label = tkinter.Label(inputFrame, text="Unit No.: ")
unit_label.grid(row=10, column=0, padx=5, pady=20)
sn_label = tkinter.Label(inputFrame, text="SerialNo: ")
sn_label.grid(row=12, column=0, padx=5, pady=20)
build = tkinter.StringVar()
build_spinbox = tkinter.Spinbox(inputFrame, values=('CV1', 'CV2', 'DV1', 'DV2', 'PV1', 'PV2', 'XXX'), textvariable=build)
build_spinbox.grid(row=8, column=1, padx=5, pady=20)
unit = tkinter.IntVar()
unit_spinbox = tkinter.Spinbox(inputFrame, from_=0, to=99999999, textvariable=unit)
unit_spinbox.grid(row=10, column=1, padx=5, pady=20)
serialno = tkinter.StringVar()
sn_entry_box = tkinter.Entry(inputFrame, textvariable=serialno)
sn_entry_box.grid(row=12, column=1, padx=5, pady=20)
sn_entry_box.delete(0)
update_serialno()
sn_entry_box.configure(state='disabled')
sn_update_btn = tkinter.Button(inputFrame, text="Update Serial No.", command=update_serialno)
sn_update_btn.grid(row=12, column=2, padx=5, pady=20)

window.mainloop()
