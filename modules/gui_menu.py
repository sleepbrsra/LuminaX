from PyQt6.QtWidgets import QPushButton, QWidget, QListWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import os
import importlib

COMETS_DIR = "comets"

class CometMenu:
    def __init__(self, parent_window, stacked_layout, empty_label, settings_menu):
        self.window = parent_window
        self.stacked_layout = stacked_layout
        self.empty_label = empty_label
        self.settings_menu = settings_menu
        self.pages = {}

        # Кнопка меню комет
        self.button = QPushButton("☰ Comets")
        self.button.setFont(QFont("Arial", 12))
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #0f0f2a;
                color: #00fff7;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover { background-color: #1a1a4d; }
        """)
        self.button.clicked.connect(self.toggle_menu)

        # Плавающее меню комет
        self.menu_frame = QFrame(self.window, Qt.WindowType.Popup)
        self.menu_frame.setStyleSheet("""
            QFrame { background-color: #0f0f2a; border: 2px solid #00fff7; border-radius: 8px; }
        """)
        self.menu_frame.setVisible(False)

        self.menu_list = QListWidget(self.menu_frame)
        self.menu_list.setStyleSheet("""
            QListWidget { background-color: transparent; color: #9d9dff; border: none; padding: 5px; }
            QListWidget::item:selected { background-color: #00fff7; color: #0d0d1a; }
        """)
        self.menu_list.currentItemChanged.connect(self.on_comet_selected)

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.menu_list)
        self.menu_frame.setLayout(layout)

        self.load_comets()

    def toggle_menu(self):
        if self.menu_frame.isVisible():
            self.menu_frame.hide()
        else:
            rows = self.menu_list.count()
            self.menu_frame.setFixedSize(200, max(50, rows * 25))
            pos = self.button.mapToGlobal(self.button.rect().bottomLeft())
            self.menu_frame.move(pos)
            self.menu_frame.show()

    def load_comets(self):
        self.menu_list.clear()
        self.menu_list.addItem("Главная")
        if not os.path.exists(COMETS_DIR):
            os.makedirs(COMETS_DIR)
        for comet_name in sorted(os.listdir(COMETS_DIR)):
            if os.path.isdir(os.path.join(COMETS_DIR, comet_name)):
                self.menu_list.addItem(comet_name.replace("_", " ").title())

    def on_comet_selected(self, current, previous):
        self.menu_frame.hide()
        if not current:
            return

        name = current.text()
        if name == "Главная":
            self.stacked_layout.setCurrentWidget(self.empty_label)
            self.settings_menu.reset()
            return

        comet_id = name.lower().replace(" ", "_")
        if comet_id not in self.pages:
            page = self.create_comet_page(comet_id)
            self.pages[comet_id] = page
            self.stacked_layout.addWidget(page)
        self.stacked_layout.setCurrentWidget(self.pages[comet_id])
        self.settings_menu.reset()

    def create_comet_page(self, comet_id):
        module_path = f"comets.{comet_id}.main"
        try:
            comet_module = importlib.import_module(module_path)
            return comet_module.create_page()
        except ModuleNotFoundError:
            lbl = QLabel(f"Комета {comet_id} пустая")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #00fff7;")
            return lbl
