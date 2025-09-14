from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QStackedLayout
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt
from modules.gui_settings import SettingsMenu
from modules.gui_menu import CometMenu

class LuminaXGUI:
    def __init__(self):
        self.app = QApplication([])
        self.window = QWidget()
        self.window.setWindowTitle("🌌 LuminaX")
        self.window.setFixedSize(800, 500)

        # Палитра
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#0d0d1a"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
        self.window.setPalette(palette)

        # --- Верхняя панель ---
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(10, 10, 10, 0)

        # --- Главная область ---
        self.stacked_layout = QStackedLayout()

        # --- Кнопка настроек ---
        self.settings = SettingsMenu(self.window)
        top_bar.addStretch()
        top_bar.addWidget(self.settings.button, alignment=Qt.AlignmentFlag.AlignRight)

        # --- Кнопка комет ---
        self.menu = CometMenu(self.window, self.stacked_layout)
        top_bar.insertWidget(0, self.menu.button, alignment=Qt.AlignmentFlag.AlignLeft)

        # --- Основной layout ---
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.addLayout(top_bar)
        self.main_layout.addLayout(self.stacked_layout)

        self.window.setLayout(self.main_layout)

    def run(self):
        self.window.show()
        self.app.exec()
