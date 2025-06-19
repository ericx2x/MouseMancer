#!/usr/bin/env python3
import os
import subprocess
import threading
import time
import atexit
import sys
import signal

import keyboard
from pathlib import Path
from pynput.mouse import Controller, Button
from pystray import Icon, MenuItem as Item, Menu
from PIL import Image, ImageDraw

from Xlib import X, display, Xutil
from Xlib.protocol import event as XEvent

# === Key Suppression Maps ===
suppressed_keycodes = {
    'w': 25, 'a': 38, 's': 39, 'd': 40, 'f': 41,
    'i': 31, 'j': 44, 'k': 45, 'l': 46, 'space': 65, 'n': 57,
}

original_keymap = {
    'w': 'w W', 'a': 'a A', 's': 's S', 'd': 'd D', 'f': 'f F',
    'i': 'i I', 'j': 'j J', 'k': 'k K', 'l': 'l L',
    'space': 'space', 'n': 'n N',
}

# === Globals ===
mouse_controller = Controller()
mouse_mode_active = False
cursor_speed = 10
pressed_keys = set()
icon = None
x_display = None
focus_trap_window = None

# === Key Groups ===
toggle_keys = {'f', 'j', 'q', 'a'}
movement_keys = {'w', 'a', 's', 'd'}
suppressed_keys = movement_keys.union({'f', 'i', 'j', 'k', 'space', 'l', 'n'})

# === Focus Trap Window (Xlib) ===
def start_focus_trap():
    global x_display, focus_trap_window
    x_display = display.Display()
    root = x_display.screen().root

    focus_trap_window = root.create_window(
        0, 0, 1, 1, 0,
        x_display.screen().root_depth,
        X.InputOutput,
        X.CopyFromParent,
        background_pixel=0,
        event_mask=X.FocusChangeMask
    )

    focus_trap_window.set_wm_name("FocusTrap")
    focus_trap_window.set_wm_hints(flags=Xutil.InputHint, input=True)
    focus_trap_window.set_wm_normal_hints(flags=Xutil.PPosition | Xutil.PSize)
    focus_trap_window.map()
    focus_trap_window.set_input_focus(X.RevertToParent, X.CurrentTime)
    x_display.sync()

def stop_focus_trap():
    global x_display, focus_trap_window
    if focus_trap_window:
        focus_trap_window.destroy()
        x_display.sync()
        focus_trap_window = None

# === Key Suppression ===
def suppress_keys():
    for key, code in suppressed_keycodes.items():
        subprocess.run(["xmodmap", "-e", f"keycode {code} = NoSymbol"], check=False)

def restore_keys():
    for key, code in suppressed_keycodes.items():
        mapping = original_keymap[key]
        subprocess.run(["xmodmap", "-e", f"keycode {code} = {mapping}"], check=False)

atexit.register(restore_keys)

# === Mouse Mode Toggle ===
def toggle_mouse_mode():
    global mouse_mode_active
    mouse_mode_active = not mouse_mode_active
    print_status()

    if mouse_mode_active:
        suppress_keys()
        start_focus_trap()
        show_overlay_message("MOUSE MODE ON")
    else:
        restore_keys()
        stop_focus_trap()
        show_overlay_message("MOUSE MODE OFF")

    update_icon()

def print_status():
    os.system('clear')
    print(f"[Mouse Mode] {'ON' if mouse_mode_active else 'OFF'}")

# === Mouse Control ===
def mouse_loop():
    global cursor_speed
    while True:
        if not mouse_mode_active:
            time.sleep(0.01)
            continue

        if 'n' in pressed_keys:
            cursor_speed = 3
        elif 'space' in pressed_keys or 'l' in pressed_keys:
            cursor_speed = 20
        else:
            cursor_speed = 10

        if 'w' in pressed_keys:
            mouse_controller.move(0, -cursor_speed)
        if 's' in pressed_keys:
            mouse_controller.move(0, cursor_speed)
        if 'a' in pressed_keys:
            mouse_controller.move(-cursor_speed, 0)
        if 'd' in pressed_keys:
            mouse_controller.move(cursor_speed, 0)

        time.sleep(0.01)

# === Keyboard Event Handling ===
def on_key_event(e):
    key = e.name

    if e.event_type == 'down':
        pressed_keys.add(key)

        if keyboard.is_pressed('caps lock') and key in toggle_keys:
            toggle_mouse_mode()
            return False

        if mouse_mode_active:
            if key == 'f':
                mouse_controller.press(Button.left)
                mouse_controller.release(Button.left)
            elif key == 'i':
                mouse_controller.press(Button.right)
                mouse_controller.release(Button.right)
            elif key == 'j':
                mouse_controller.scroll(0, -1)
            elif key == 'k':
                mouse_controller.scroll(0, 1)

            if key in suppressed_keys:
                return False

    elif e.event_type == 'up':
        if key in pressed_keys:
            pressed_keys.remove(key)

    if mouse_mode_active and key in suppressed_keys:
        return False

    return None

# === System Tray ===
def show_overlay_message(message):
    script_path = Path(__file__).parent / "overlay.py"
    subprocess.Popen(["python3", str(script_path), message])

def create_image(active):
    color = "green" if active else "gray"
    image = Image.new("RGB", (64, 64), color)
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, 56, 56), fill=color, outline="black")
    return image

def update_icon():
    if icon:
        icon.icon = create_image(mouse_mode_active)

def tray_thread():
    global icon
    icon = Icon("MouseMancer")
    icon.menu = Menu(
        Item("Toggle Mouse Mode", lambda: toggle_mouse_mode()),
        Item("Exit", lambda: exit_program()),
    )
    icon.icon = create_image(mouse_mode_active)
    icon.run()

# === Exit Handlers ===
def exit_program():
    restore_keys()
    stop_focus_trap()
    if icon:
        icon.stop()
    sys.exit()

def signal_handler(sig, frame):
    restore_keys()
    stop_focus_trap()
    exit_program()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGQUIT, signal_handler)

# === Main ===
if __name__ == "__main__":
    print("MouseMancer Started - Press Caps Lock + F/J/Q/A to toggle mouse mode.")
    print("NOTE: You MUST run this script with sudo on Linux X11 for suppression to work.")

    threading.Thread(target=mouse_loop, daemon=True).start()
    threading.Thread(target=tray_thread, daemon=True).start()
    keyboard.hook(on_key_event)
    keyboard.wait()

