from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer
from pynput.mouse import Controller, Button
import string

GRID_ROWS = 22
GRID_COLS = 22
PRECISION_KEYS = {
    'q': (0, 0), 'w': (0, 1), 'e': (0, 2),
    'a': (1, 0), 's': (1, 1), 'd': (1, 2),
    'z': (2, 0), 'x': (2, 1), 'c': (2, 2),
    'u': (0, 0), 'i': (0, 1), 'o': (0, 2),
    'j': (1, 0), 'k': (1, 1), 'l': (1, 2),
    'm': (2, 0), ',': (2, 1), '.': (2, 2),
}
mouse_controller = Controller()

class GridOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 220);")
        self.setFocusPolicy(Qt.StrongFocus)

        self.screen_geom = self.screen().geometry()
        self.screen_width = self.screen_geom.width()
        self.screen_height = self.screen_geom.height()

        self.labels = {}
        self.key_buffer = ""
        self.precision_mode = False
        self.selected_cell = None
        self.highlight_label = None

        grid = QGridLayout()
        grid.setSpacing(0)
        grid.setContentsMargins(0, 0, 0, 0)
        self.setLayout(grid)

        keys = list(string.ascii_lowercase[:GRID_ROWS])
        font_main = QFont("Monospace", 18)
        font_main.setBold(True)

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                key = keys[r] + keys[c]
                label = QLabel(key)
                label.setObjectName(key)
                label.setFont(font_main)
                label.setAlignment(Qt.AlignCenter)
                label.setMinimumSize(48, 48)  # Increase cell size
                label.setStyleSheet("""
                    background-color: rgba(0, 0, 0, 120);
                    color: lime;
                    border: 1px solid white;
                """)
                self.labels[key] = label
                grid.addWidget(label, r, c)

        self.grabKeyboard()
        self.showFullScreen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            return

        char = event.text().lower()
        if not char.isalpha():
            return

        if self.precision_mode:
            if char in PRECISION_KEYS:
                self.precision_click(char)
            return

        self.key_buffer += char
        if len(self.key_buffer) == 2:
            key = self.key_buffer
            self.key_buffer = ""
            if key in self.labels:
                self.select_cell(key)

    def select_cell(self, key):
        if self.highlight_label and self.highlight_label != self.labels[key]:
            original_key = self.highlight_label.objectName()
            self.highlight_label.setText(original_key)
            self.highlight_label.setFont(QFont("Monospace", 18, QFont.Bold))
            self.highlight_label.setAlignment(Qt.AlignCenter)
            self.highlight_label.setStyleSheet("""
                background-color: rgba(0, 0, 0, 120);
                color: lime;
                border: 1px solid white;
            """)

        self.highlight_label = self.labels[key]
        self.highlight_label.setFont(QFont("Monospace", 10))
        self.highlight_label.setAlignment(Qt.AlignCenter)
        self.highlight_label.setText("Q W E\nA S D\nZ X C")
        self.highlight_label.setStyleSheet("""
            background-color: rgba(255, 215, 0, 200);
            color: black;
            border: 2px solid white;
            padding: 2px;
        """)

        self.selected_cell = self.get_cell_coords(key)
        self.precision_mode = True

    def get_cell_coords(self, key):
        keys = list(string.ascii_lowercase[:GRID_ROWS])
        row = keys.index(key[0])
        col = keys.index(key[1])
        return (row, col)

    def precision_click(self, key):
        row, col = self.selected_cell
        cell_width = self.screen_width / GRID_COLS
        cell_height = self.screen_height / GRID_ROWS
        base_x = col * cell_width
        base_y = row * cell_height

        sub_r, sub_c = PRECISION_KEYS[key]
        sub_x = (sub_c + 0.5) * (cell_width / 3)
        sub_y = (sub_r + 0.5) * (cell_height / 3)

        x = int(base_x + sub_x)
        y = int(base_y + sub_y)

        self.hide()
        QTimer.singleShot(10, lambda: self.move_and_click(x, y))
        QTimer.singleShot(20, self.close)

    def move_and_click(self, x, y):
        mouse_controller.position = (x, y)
        QTimer.singleShot(5, lambda: mouse_controller.click(Button.left))

