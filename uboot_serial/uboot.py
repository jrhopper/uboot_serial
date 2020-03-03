"""
uboot.py
This script contains supporting functions for updating firmware on the device.
"""

import time
import datetime
import tkinter

def read_until(com, string, timeout=5):
    """
    Read character by character until the desired string is found up until the timeout in seconds.
    Prints all characters read.

    Parameters:
        com                 The serial port
        string              The desired search string
        timeout             The amount of time to search in seconds
    Returns:
        (string)            Returns text if the string was found or None if timeout elapsed.
    """
    text = ""
    start = time.time()
    com.reset_input_buffer()
    while (time.time() - start) < timeout:
        char = com.read().decode('ascii', 'ignore')
        text += char
        if string in text:
            print(text)
            return text
    print(text)
    return None

def readline_until(com, string, timeout=5):
    """
    Read line by line until the desired string is found up until the timeout in seconds.
    Prints all characters read.

    Parameters:
        com                 The serial port
        string              The desired search string
        timeout             The amount of time to search in seconds
    Returns:
        (string)            Returns text if the string was found or None if timeout elapsed.
    """
    text = ""
    start = time.time()
    com.reset_input_buffer()
    while (time.time() - start) < timeout:
        line = com.readline().decode('ascii', 'ignore')
        text += line
        if string in text:
            print(text)
            return text
    print(text)
    return None

def send_cmd(com, command):
    """
    Send a command at the prompt (u-boot or root). Does not wait for next prompt.

    Parameters:
        com                 The serial port
        command             The command string to send at prompt
    Returns:
        none
    """
    command = command + "\r\n"
    com.write(command.encode('ascii'))

def check_prompt(com):
    """
    Checks if a prompt exists and if so, which prompt (u-boot, login, or root).
    Prints all characters read.

    Parameters:
        com                 The serial port
    Returns:
        (str)               A string value: "uboot" | "login" | "root"
    """
    prompt_found = False
    prompt = ""
    if not prompt_found:
        send_cmd(com, "")
        send_cmd(com, "")
        if readline_until(com, "=>", timeout=1):
            prompt = "uboot"
            prompt_found = True
    if not prompt_found:
        send_cmd(com, "")
        send_cmd(com, "")
        if readline_until(com, "ccimx6sbc login:", timeout=1):
            prompt = "login"
            prompt_found = True
    if not prompt_found:
        send_cmd(com, "")
        send_cmd(com, "")
        if readline_until(com, "root@ccimx6sbc:", timeout=1):
            prompt = "root"
            prompt_found = True
    return prompt

def boot_to_uboot(com, reset=True):
    """
    Checks prompt and reboots appropriately. Stops autoboot. Waits for uboot prompt.
    Prints all characters read.

    Parameters:
        com                 The serial port
        reset               If True, the CPU resets even if already at u-boot.
                            If False, the CPU remains at u-boot prompt if already there.
                            Default is True.
    Returns:
        (boolean)           Returns True if uboot prompt is ready or False if not.
    """
    prompt = check_prompt(com)
    if prompt == "uboot":
        if reset:
            send_cmd(com, "reset")
        else:
            return True
    elif prompt == "login":
        success = login(com)
        if success:
            send_cmd(com, "reboot")
    elif prompt == "root":
        send_cmd(com, "reboot")
    else:
        return False
    read_until(com, "Hit any key to stop autoboot: ", timeout=20)
    send_cmd(com, "")
    prompt = check_prompt(com)
    if prompt == "uboot":
        return True
    return False

def login(com, root_psswd="Allergen_lock"):
    """
    Logs in as root user. Assumes already at login prompt.

    Parameters:
        com                 The serial port
    Returns:
        (boolean)           Returns True if root login succeeds. Returns False if not.
    """
    send_cmd(com, "root")
    read_until(com, "Password:")
    send_cmd(com, root_psswd)
    prompt = check_prompt(com)
    if prompt == "root":
        return True
    return False

def boot_to_login(com, reboot=False):
    """
    Checks prompt and reboots appropriately. Waits for kernel startup.
    Stops at login prompt.
    Prints all characters read.

    Parameters:
        com                 The serial port
        reboot              If True, reboots the system regardless of prompt.
                            If False, remains at root prompt without reboot.
    Returns:
        (boolean)           Returns True if login prompt is ready or False if not.
    """
    prompt = check_prompt(com)
    if prompt == "uboot":
        send_cmd(com, "reset")
    elif prompt == "login":
        return True
    elif prompt == "root":
        if reboot:
            send_cmd(com, "reboot")
        else:
            send_cmd(com, "exit")
    else:
        return False
    read_until(com, "ccimx6sbc login: ", timeout=40)
    send_cmd(com, "")
    prompt = check_prompt(com)
    if prompt == "login":
        return True
    return False

def boot_to_root(com, root_psswd="Allergen_lock", reboot=False):
    """
    Checks prompt and reboots appropriately. Waits for kernel startup. Logs in as root.
    Stops at root prompt.
    Prints all characters read.

    Parameters:
        com                 The serial port
        root_psswd          Root password. Default = "Allergen_lock"
        reboot              If True, reboots the system regardless of prompt.
                            If False, remains at root prompt without reboot.
    Returns:
        (boolean)           Returns True if root prompt is ready or False if not.
    """
    prompt_ready = False
    prompt = check_prompt(com)
    if prompt == "uboot":
        send_cmd(com, "reset")
        read_until(com, "ccimx6sbc login: ", timeout=40)
        success = login(com, root_psswd=root_psswd)
        if success:
            prompt_ready = True
    elif prompt == "login":
        success = login(com, root_psswd=root_psswd)
        if success:
            prompt_ready = True
    elif prompt == "root":
        if reboot:
            send_cmd(com, "reboot")
            read_until(com, "ccimx6sbc login: ", timeout=60)
            success = login(com, root_psswd=root_psswd)
            if success:
                prompt_ready = True
        else:
            prompt_ready = True
    return prompt_ready

def log(text, print_log=False, widget=None):
    """
    Similar to print(), but with timestamping. If print_log is True, then log is printed
    to terminal. Returns log_data with a timestamp appended.

    Parameters:
        text                The string to be logged
        print_log           If True, prints to terminal. Default=False
    Returns:
        log_data            The string of timestampped log data
    """
    timestamp = datetime.datetime.now().strftime("%b-%d-%Y-%H-%M-%S").upper()
    log_data = "[{}]    ".format(timestamp) + text
    if print_log:
        print(log_data)
    if widget is not None:
        widget.configure(state='normal')
        widget.insert(tkinter.INSERT, log_data + '\n')
        widget.configure(state='disabled')
        widget.yview_moveto(1)
    return log_data
