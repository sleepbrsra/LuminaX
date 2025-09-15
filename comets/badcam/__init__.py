from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import subprocess

CONFIGS = {
    "Light Version": "a.py",
    "Astronomi": "b.py",
    "Pixel": "bad",
    "Funny Mode": "main.py"
}

def create_page():
    """Возвращает QWidget с интерфейсом кометы BadCam."""
    page = QWidget()
    layout = QVBoxLayout()
    layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

    title = QLabel("🌠 Комета: BadCam")
    title.setFont(QFont("Arial", 16))
    layout.addWidget(title)

    desc = QLabel("Виртуальная веб-камера с эффектами. Можно выбирать конфиг и запускать виртуальную камеру.")
    layout.addWidget(desc)

    # ------------------ Выбор конфига ------------------
    config_combo = QComboBox()
    config_combo.addItems(CONFIGS.keys())
    layout.addWidget(config_combo)

    # ------------------ Название виртуальной камеры ------------------
    cam_name_combo = QComboBox()
    cam_name_combo.addItems(["BadCam", "BadCamX", "MyCam"])
    layout.addWidget(cam_name_combo)

    # ------------------ Кнопка старт/стоп ------------------
    running = {"state": False}

    def toggle_comet():
        if not running["state"]:
            config = CONFIGS[config_combo.currentText()]
            cam_name = cam_name_combo.currentText()
            # запуск виртуальной камеры Linux
            try:
                subprocess.run([
                    "sudo","modprobe","v4l2loopback",
                    "devices=1",
                    f"video_nr=2",
                    f'card_label="{cam_name}"',
                    "exclusive_caps=1"
                ], check=True)
            except Exception as e:
                print("Ошибка запуска виртуальной камеры:", e)

            print(f"Запущен конфиг: {config}")
            running["state"] = True
            btn.setText("Остановить BadCam")
        else:
            # остановка кометы
            print("BadCam остановлена!")
            running["state"] = False
            btn.setText("Запустить BadCam")

    btn = QPushButton("Запустить BadCam")
    btn.clicked.connect(toggle_comet)
    layout.addWidget(btn)

    page.setLayout(layout)
    return page
