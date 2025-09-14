from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

def create_page():
    """Возвращает QWidget с интерфейсом кометы."""
    page = QWidget()
    layout = QVBoxLayout()
    layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

    title = QLabel("🌠 Комета: Test")
    title.setFont(QFont("Arial", 16))
    layout.addWidget(title)

    desc = QLabel("Это пример внутренностей кометы Test.")
    layout.addWidget(desc)

    btn = QPushButton("Запустить Test")
    btn.clicked.connect(lambda: print("Комета Test запущена!"))
    layout.addWidget(btn)

    page.setLayout(layout)
    return page
