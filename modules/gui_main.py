from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedLayout, QLabel
)
from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtCore import Qt
from modules.gui_settings import SettingsMenu
from modules.gui_menu import CometMenu  # твой рабочий модуль с кометами

class LuminaXGUI:
    def __init__(self):
        self.app = QApplication([])
        self.window = QWidget()
        self.window.setWindowTitle("🌌 LuminaX")
        self.window.setFixedSize(800, 500)

        # --- Палитра ---
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#0d0d1a"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
        self.window.setPalette(palette)

        # --- Верхняя панель ---
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(10, 10, 10, 0)

        # --- Главное содержимое ---
        self.stacked_layout = QStackedLayout()

        # --- Главная страница ---
        self.empty_label = QLabel("🌌 Добро пожаловать в LuminaX!\nВыберите комету сверху, чтобы начать.")
        self.empty_label.setFont(QFont("Arial", 16))
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #00fff7;")
        self.stacked_layout.addWidget(self.empty_label)

        # --- Кнопка комет ---
        self.settings_btn = SettingsMenu.create_button()
        self.settings_menu = SettingsMenu(self.window, self.stacked_layout, self.settings_btn)
        self.menu = CometMenu(self.window, self.stacked_layout, self.empty_label, self.settings_menu)


        top_bar.addWidget(self.menu.button, alignment=Qt.AlignmentFlag.AlignLeft)

        # --- Кнопка настроек ---
        self.settings_btn = SettingsMenu.create_button()
        top_bar.addStretch()
        top_bar.addWidget(self.settings_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self.settings = SettingsMenu(self.window, self.stacked_layout, self.settings_btn)

        # --- Основной layout ---
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.addLayout(top_bar)
        self.main_layout.addLayout(self.stacked_layout)
        self.window.setLayout(self.main_layout)

    def run(self):
        self.window.show()
        self.app.exec()
