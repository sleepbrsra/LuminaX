from PyQt6.QtWidgets import QPushButton, QFrame, QListWidget, QVBoxLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class SettingsMenu:
    def __init__(self, parent_window):
        self.window = parent_window

        # --- Кнопка ---
        self.button = QPushButton("⚙️")
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
        self.button.clicked.connect(self.toggle_settings)

        # --- Меню ---
        self.settings_frame = QFrame(self.window)
        self.settings_frame.setFrameShape(QFrame.Shape.Box)
        self.settings_frame.setStyleSheet("""
            QFrame { background-color: #0f0f2a; border: 2px solid #00fff7; border-radius: 8px; }
        """)
        self.settings_frame.setVisible(False)

        self.settings_list = QListWidget(self.settings_frame)
        self.settings_list.setStyleSheet("""
            QListWidget { background-color: transparent; color: #9d9dff; border: none; padding: 5px; }
            QListWidget::item:selected { background-color: #00fff7; color: #0d0d1a; }
        """)
        self.settings_list.addItems(["Settings", "Exit"])
        self.settings_list.currentItemChanged.connect(self.on_setting_selected)

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.settings_list)
        self.settings_frame.setLayout(layout)

    def toggle_settings(self):
        if self.settings_frame.isVisible():
            self.settings_frame.hide()
        else:
            rows = self.settings_list.count()
            self.settings_frame.setFixedSize(150, max(50, rows*25))
            btn_pos = self.button.mapToGlobal(self.button.rect().bottomLeft())
            win_pos = self.window.mapFromGlobal(btn_pos)
            if win_pos.x() + self.settings_frame.width() > self.window.width():
                win_pos.setX(self.window.width() - self.settings_frame.width() - 5)
            self.settings_frame.move(win_pos)
            self.settings_frame.show()

    def on_setting_selected(self, current, previous):
        self.settings_frame.hide()
        if current:
            setting = current.text()
            if setting == "Exit":
                self.window.close()
            elif setting == "Settings":
                print("Открываем настройки...")
        self.settings_list.clearSelection()
