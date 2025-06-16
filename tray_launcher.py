# tray_launcher.py
import sys
import threading
from PyQt5.QtWidgets import QApplication
from grid_overlay import GridOverlay
from pynput import keyboard as keylisten
from pystray import Icon, MenuItem as Item, Menu
from PIL import Image, ImageDraw

app = QApplication(sys.argv)
overlay = None

def toggle_overlay():
    global overlay
    if overlay is None or not overlay.isVisible():
        overlay = GridOverlay()
        overlay.showFullScreen()
    else:
        overlay.close()
        overlay = None

def hotkey_listener():
    combo = {keylisten.Key.cmd, keylisten.KeyCode(char='j')}
    current = set()

    def on_press(key):
        if key in combo:
            current.add(key)
        if current == combo:
            toggle_overlay()

    def on_release(key):
        current.discard(key)

    with keylisten.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

def create_image():
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Draw mouse body (oval)
    draw.ellipse([18, 10, 46, 38], fill=(200, 200, 200), outline="black")

    # Draw mouse buttons (a line splitting the top)
    draw.line([32, 10, 32, 24], fill="black", width=1)

    # Draw mouse wheel (small circle)
    draw.ellipse([29, 25, 35, 31], fill="darkgray", outline="black")

    # Optional: draw tail
    draw.line([32, 38, 32, 60], fill="gray", width=2)

    return image

def quit_app(icon, item):
    icon.stop()
    sys.exit()

# Start hotkey thread
threading.Thread(target=hotkey_listener, daemon=True).start()

# Create tray icon
icon = Icon("GridMouse")
icon.icon = create_image()
icon.menu = Menu(Item("Quit", quit_app))
icon.run()
