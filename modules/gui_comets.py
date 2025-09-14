from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

def create_comet_page(comet_id):
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
        QPushButton:hover { background-color: #1a1a4d; }
        QPushButton:pressed { background-color: #00fff7; color: #0d0d1a; }
    """)
    btn.clicked.connect(lambda: print(f"Комета {comet_id} запущена!"))
    layout.addWidget(btn)

    page.setLayout(layout)
    return page
