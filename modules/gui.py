import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QStackedLayout, QListWidget, QListWidgetItem, QFrame
)
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtCore import Qt, QPoint

COMETS_DIR = "comets"

class LuminaXGUI:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = QWidget()
        self.window.setWindowTitle("🌌 LuminaX")
        self.window.setFixedSize(800, 500)

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#0d0d1a"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
        self.window.setPalette(palette)

        # --- Верхняя панель ---
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(10, 10, 10, 0)

        # Кнопка меню комет
        self.menu_btn = QPushButton("☰ Кометы")
        self.menu_btn.setFont(QFont("Arial", 12))
        self.menu_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f0f2a;
                color: #00fff7;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #1a1a4d;
            }
        """)
        self.menu_btn.clicked.connect(self.toggle_menu)
        top_bar.addWidget(self.menu_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        top_bar.addStretch()

        # Кнопка настроек справа
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setFont(QFont("Arial", 12))
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f0f2a;
                color: #00fff7;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #1a1a4d;
            }
        """)
        self.settings_btn.clicked.connect(self.toggle_settings)
        top_bar.addWidget(self.settings_btn, alignment=Qt.AlignmentFlag.AlignRight)

        # --- Главная панель ---
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(top_bar)

        # Основная область для контента
        self.stacked_layout = QStackedLayout()
        self.stacked_widget = QWidget()
        self.stacked_widget.setLayout(self.stacked_layout)
        self.main_layout.addWidget(self.stacked_widget)

        self.empty_label = QLabel("Выберите комету сверху")
        self.empty_label.setFont(QFont("Arial", 14))
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stacked_layout.addWidget(self.empty_label)

        self.comet_pages = {}
        self.window.setLayout(self.main_layout)

        # --- Плавающее меню комет ---
        self.menu_frame = QFrame(self.window)
        self.menu_frame.setFrameShape(QFrame.Shape.Box)
        self.menu_frame.setStyleSheet("""
            QFrame {
                background-color: #0f0f2a;
                border: 2px solid #00fff7;
                border-radius: 8px;
            }
        """)
        self.menu_frame.setVisible(False)
        self.menu_list = QListWidget(self.menu_frame)
        self.menu_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                color: #9d9dff;
                border: none;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #00fff7;
                color: #0d0d1a;
            }
        """)
        self.menu_list.currentItemChanged.connect(self.on_comet_selected)
        self.load_comets()
        menu_layout = QVBoxLayout()
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.addWidget(self.menu_list)
        self.menu_frame.setLayout(menu_layout)

        # --- Плавающее меню настроек ---
        self.settings_frame = QFrame(self.window)
        self.settings_frame.setFrameShape(QFrame.Shape.Box)
        self.settings_frame.setStyleSheet("""
            QFrame {
                background-color: #0f0f2a;
                border: 2px solid #00fff7;
                border-radius: 8px;
            }
        """)
        self.settings_frame.setVisible(False)

        self.settings_list = QListWidget(self.settings_frame)
        self.settings_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                color: #9d9dff;
                border: none;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #00fff7;
                color: #0d0d1a;
            }
        """)
        self.settings_list.addItems(["Settings", "Exit"])
        self.settings_list.currentItemChanged.connect(self.on_setting_selected)
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.addWidget(self.settings_list)
        self.settings_frame.setLayout(settings_layout)

    # --- Меню комет ---
    def toggle_menu(self):
        if self.menu_frame.isVisible():
            self.menu_frame.hide()
        else:
            rows = self.menu_list.count()
            item_height = 25
            self.menu_frame.setFixedSize(200, max(50, rows * item_height))
            btn_pos = self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft())
            win_pos = self.window.mapFromGlobal(btn_pos)
            self.menu_frame.move(win_pos)
            self.menu_frame.show()
            self.settings_frame.hide()

    # --- Меню настроек ---
    def toggle_settings(self):
        if self.settings_frame.isVisible():
            self.settings_frame.hide()
        else:
            rows = self.settings_list.count()
            item_height = 25
            self.settings_frame.setFixedSize(150, max(50, rows * item_height))
            
            # позиция кнопки в глобальных координатах
            btn_pos = self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomLeft())
            win_pos = self.window.mapFromGlobal(btn_pos)
            
            # проверяем выход за правый край
            if win_pos.x() + self.settings_frame.width() > self.window.width():
                win_pos.setX(self.window.width() - self.settings_frame.width() - 5)  # отступ 5px
            
            self.settings_frame.move(win_pos)
            self.settings_frame.show()
            self.menu_frame.hide()


    def load_comets(self):
        if not os.path.exists(COMETS_DIR):
            os.makedirs(COMETS_DIR)
        self.menu_list.clear()
        for comet_name in sorted(os.listdir(COMETS_DIR)):
            if os.path.isdir(os.path.join(COMETS_DIR, comet_name)):
                item = QListWidgetItem(comet_name.replace("_", " ").title())
                item.setData(Qt.ItemDataRole.UserRole, comet_name)
                self.menu_list.addItem(item)

    def on_comet_selected(self, current, previous):
        self.menu_frame.hide()
        if current:
            comet_id = current.data(Qt.ItemDataRole.UserRole)
            if comet_id not in self.comet_pages:
                page = self.create_comet_page(comet_id)
                self.comet_pages[comet_id] = page
                self.stacked_layout.addWidget(page)
            self.stacked_layout.setCurrentWidget(self.comet_pages[comet_id])
        else:
            self.stacked_layout.setCurrentWidget(self.empty_label)

    def on_setting_selected(self, current, previous):
        self.settings_frame.hide()
        if current:
            setting = current.text()
            if setting == "Exit":
                self.window.close()
            elif setting == "Settings":
                print("Открываем настройки...")  # здесь можно добавить окно настроек
        self.settings_list.clearSelection()

    def create_comet_page(self, comet_id):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        title = QLabel(f"🌠 Комета: {comet_id.replace('_', ' ').title()}")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #00fff7;")
        layout.addWidget(title)

        desc = QLabel(f"Здесь будут функции модуля {comet_id}.")
        desc.setFont(QFont("Arial", 12))
        desc.setStyleSheet("color: #9d9dff;")
        layout.addWidget(desc)

        btn = QPushButton(f"Запустить {comet_id}")
        btn.setFont(QFont("Arial", 12))
        btn.setStyleSheet("""
            QPushButton {
                background-color: #0f0f2a;
                color: #00fff7;
                border-radius: 8px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #1a1a4d;
            }
            QPushButton:pressed {
                background-color: #00fff7;
                color: #0d0d1a;
            }
        """)
        btn.clicked.connect(lambda: print(f"Комета {comet_id} запущена!"))
        layout.addWidget(btn)

        page.setLayout(layout)
        return page

    def run(self):
        self.window.show()
        sys.exit(self.app.exec())
