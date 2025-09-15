from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit
from PyQt6.QtGui import QFont, QImage, QPixmap
from PyQt6.QtCore import Qt, QTimer
import subprocess
import os
import cv2


class BadCamComet:
    def __init__(self):
        self.proc = None
        self.vcam_name = "BadCam"
        self.active_config = None
        self.vcam_active = False
        self.video_nr = 2  # номер устройства

    # ------------------ Виртуальная камера ------------------
    def start_virtual_camera(self):
        if os.name != "posix":
            return
        try:
            subprocess.run("sudo modprobe -r v4l2loopback", shell=True)

            cmd = (
                f"sudo modprobe v4l2loopback devices=1 video_nr={self.video_nr} "
                f"card_label=\"{self.vcam_name}\" exclusive_caps=1"
            )
            subprocess.run(cmd, shell=True, check=True)
            self.vcam_active = True
            print(f"Виртуальная камера {self.vcam_name} запущена на /dev/video{self.video_nr}")
        except subprocess.CalledProcessError as e:
            print("Ошибка запуска виртуальной камеры:", e)

    def stop_virtual_camera(self):
        if os.name != "posix":
            return
        try:
            subprocess.run("sudo modprobe -r v4l2loopback", shell=True, check=True)
            self.vcam_active = False
            print("Виртуальная камера остановлена")
        except subprocess.CalledProcessError as e:
            print("Ошибка остановки виртуальной камеры:", e)

    # ------------------ Конфиги ------------------
    def launch_config(self):
        if self.proc:
            self.stop_config()
        if not self.active_config:
            return
        try:
            configs_dir = os.path.join(os.path.dirname(__file__), "configs")
            script_path = os.path.join(configs_dir, self.active_config)
            self.proc = subprocess.Popen(["python3", script_path])
            print(f"Запущен конфиг: {self.active_config}")
        except Exception as e:
            print("Ошибка запуска конфига:", e)

    def stop_config(self):
        if self.proc:
            self.proc.terminate()
            self.proc.wait()
            print(f"Остановлен конфиг: {self.active_config}")
            self.proc = None


# ------------------ Окно превью ------------------
class PreviewWindow(QWidget):
    def __init__(self, video_nr=2):
        super().__init__()
        self.setWindowTitle("Превью виртуальной камеры")
        self.resize(320, 240)

        self.label = QLabel("Загрузка превью...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.cap = cv2.VideoCapture(f"/dev/video{video_nr}")
        if not self.cap.isOpened():
            self.label.setText("Не удалось открыть виртуальную камеру")
            return

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        qimg = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qimg).scaled(
            self.label.width(), self.label.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        ))

    def closeEvent(self, event):
        if hasattr(self, "timer"):
            self.timer.stop()
        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()
        event.accept()


def create_page():
    page = QWidget()
    layout = QVBoxLayout()
    layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

    comet = BadCamComet()
    page.preview_window = None  # храним ссылку на окно превью

    # ------------------ Заголовок ------------------
    title = QLabel("🌠 Комета: BadCam")
    title.setFont(QFont("Arial", 16))
    layout.addWidget(title)

    # ------------------ Виртуальная камера ------------------
    vcam_label = QLabel("Имя виртуальной камеры:")
    vcam_input = QLineEdit()
    vcam_input.setText("BadCam")
    layout.addWidget(vcam_label)
    layout.addWidget(vcam_input)

    vcam_btn = QPushButton("Вкл/Выкл виртуальную камеру")
    layout.addWidget(vcam_btn)

    status_vcam = QLabel("VCam статус: Выключена")
    layout.addWidget(status_vcam)

    def toggle_vcam():
        if not comet.vcam_active:
            comet.vcam_name = vcam_input.text().strip() or "BadCam"
            comet.start_virtual_camera()
            status_vcam.setText(f"VCam статус: Включена ({comet.vcam_name})")
        else:
            comet.stop_virtual_camera()
            status_vcam.setText("VCam статус: Выключена")

    vcam_btn.clicked.connect(toggle_vcam)

    # ------------------ Конфиги ------------------
    layout.addWidget(QLabel("Выберите конфиг:"))
    configs_dir = os.path.join(os.path.dirname(__file__), "configs")
    COMF_FILES = [f for f in os.listdir(configs_dir) if f.endswith(".py")]

    config_combo = QComboBox()
    config_combo.addItems(COMF_FILES)
    layout.addWidget(config_combo)

    toggle_btn = QPushButton("Включить комету")
    layout.addWidget(toggle_btn)

    status_label = QLabel("Статус: Выключена")
    layout.addWidget(status_label)

    def toggle_comet():
        if toggle_btn.text() == "Включить комету":
            comet.active_config = config_combo.currentText()
            comet.launch_config()
            toggle_btn.setText("Выключить комету")
            status_label.setText(f"Статус: Включена ({comet.active_config})")
        else:
            comet.stop_config()
            toggle_btn.setText("Включить комету")
            status_label.setText("Статус: Выключена")

    toggle_btn.clicked.connect(toggle_comet)

    # ------------------ Кнопка превью ------------------
    preview_btn = QPushButton("Превью виртуальной камеры")
    layout.addWidget(preview_btn)

    def toggle_preview():
        if page.preview_window and page.preview_window.isVisible():
            page.preview_window.close()
            page.preview_window = None
        else:
            win = PreviewWindow(comet.video_nr)
            win.show()
            page.preview_window = win

    preview_btn.clicked.connect(toggle_preview)

    page.setLayout(layout)
    return page
