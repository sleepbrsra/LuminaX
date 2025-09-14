from PyQt6.QtWidgets import QPushButton, QWidget, QListWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class SettingsMenu:
    @staticmethod
    def create_button():
        btn = QPushButton("⚙️")
        btn.setFont(QFont("Arial", 12))
        btn.setStyleSheet("""
            QPushButton {
                background-color: #0f0f2a;
                color: #00fff7;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover { background-color: #1a1a4d; }
        """)
        return btn

    def __init__(self, parent_window, stacked_layout, settings_btn: QPushButton):
        self.window = parent_window
        self.stacked_layout = stacked_layout
        self.settings_btn = settings_btn

        # --- Плавающее меню ---
        self.settings_frame = QWidget(self.window, Qt.WindowType.Popup)
        self.settings_frame.setStyleSheet("""
            QWidget { background-color: #0f0f2a; border: 2px solid #00fff7; border-radius: 8px; }
        """)
        self.settings_frame.setVisible(False)

        self.settings_list = QListWidget(self.settings_frame)
        self.settings_list.setStyleSheet("""
            QListWidget { background-color: transparent; color: #9d9dff; border: none; padding: 5px; }
            QListWidget::item:selected { background-color: #00fff7; color: #0d0d1a; }
        """)
        self.settings_list.addItems(["Настройки", "Выход"])
        # <-- меняем обработчик на itemClicked
        self.settings_list.itemClicked.connect(self.on_setting_selected_click)

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.settings_list)
        self.settings_frame.setLayout(layout)

        # --- Страница настроек ---
        self.settings_page = QWidget()
        page_layout = QVBoxLayout()
        page_label = QLabel("⚙️ Страница настроек LuminaX")
        page_label.setFont(QFont("Arial", 16))
        page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_layout.addWidget(page_label)
        self.settings_page.setLayout(page_layout)
        self.stacked_layout.addWidget(self.settings_page)

        # --- Подключаем кнопку ---
        self.settings_btn.clicked.connect(self.toggle_settings)

    def toggle_settings(self):
        if self.settings_frame.isVisible():
            self.settings_frame.hide()
        else:
            # Сбрасываем выделение, чтобы можно было кликнуть повторно
            self.settings_list.clearSelection()

            rows = self.settings_list.count()
            self.settings_frame.setFixedSize(150, max(50, rows*25))
            btn_pos = self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomLeft())
            self.settings_frame.move(btn_pos)
            self.settings_frame.show()

    def on_setting_selected_click(self, item):
        """Обработка клика по элементу меню настроек"""
        self.settings_frame.hide()
        # Сбрасываем выделение
        self.settings_list.clearSelection()
        if item.text() == "Выход":
            self.window.close()
        elif item.text() == "Настройки":
            self.stacked_layout.setCurrentWidget(self.settings_page)

    def reset(self):
        """Сбрасываем состояние меню настроек"""
        self.settings_list.clearSelection()
        self.settings_frame.hide()
