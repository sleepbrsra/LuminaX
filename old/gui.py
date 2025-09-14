# gui.py
import sys
import numpy as np
from PySide6 import QtWidgets, QtCore, QtGui
import cv2
from core import add_noise, jpeg_artifacts, simulate_dead_pixels, rolling_shutter, vignette, local_posterize
from cam import CameraManager

class BadCamGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultra Bad Chinese Cam GUI")
        self.resize(500, 700)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.cam_manager = CameraManager()
        self.running = False
        self.frame_idx = 0

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # --- Платформа ---
        self.platform_combo = QtWidgets.QComboBox()
        self.platform_combo.addItems(["Windows", "Linux"])
        layout.addWidget(QtWidgets.QLabel("Выберите платформу"))
        layout.addWidget(self.platform_combo)

        # --- Камеры ---
        self.cam_combo = QtWidgets.QComboBox()
        layout.addWidget(QtWidgets.QLabel("Выберите камеру"))
        layout.addWidget(self.cam_combo)

        self.refresh_btn = QtWidgets.QPushButton("Обновить список камер")
        self.refresh_btn.clicked.connect(self.refresh_cameras)
        layout.addWidget(self.refresh_btn)

        # --- FPS ---
        self.fps_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.fps_slider.setRange(1, 30)
        self.fps_slider.setValue(10)
        layout.addWidget(QtWidgets.QLabel("FPS"))
        layout.addWidget(self.fps_slider)

        # --- JPEG ---
        self.quality_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.quality_slider.setRange(5, 50)
        self.quality_slider.setValue(18)
        layout.addWidget(QtWidgets.QLabel("JPEG качество"))
        layout.addWidget(self.quality_slider)

        # --- Dead pixels ---
        self.dead_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.dead_slider.setRange(0, 1000)
        self.dead_slider.setValue(2)
        layout.addWidget(QtWidgets.QLabel("Dead pixels density"))
        layout.addWidget(self.dead_slider)

        # --- Старт/Стоп ---
        self.start_btn = QtWidgets.QPushButton("Старт")
        self.start_btn.clicked.connect(self.toggle)
        layout.addWidget(self.start_btn)

        # --- Превью ---
        self.label = QtWidgets.QLabel()
        self.label.setFixedSize(320, 240)
        layout.addWidget(self.label)

        self.refresh_cameras()

    def refresh_cameras(self):
        platform = self.platform_combo.currentText()
        self.cam_manager.platform = platform
        cams = self.cam_manager.list_cameras()
        self.cam_combo.clear()
        if cams:
            self.cam_combo.addItems(cams)
        else:
            self.cam_combo.addItem("0")  # пустая заглушка

    def toggle(self):
        if not self.running:
            cam_idx = int(self.cam_combo.currentText())
            self.cam_manager.open_camera(cam_idx)
            self.running = True
            self.start_btn.setText("Стоп")
            self.timer.start(1000 // self.fps_slider.value())
        else:
            self.running = False
            self.timer.stop()
            self.cam_manager.close()
            self.start_btn.setText("Старт")

    def update_frame(self):
        if not self.running:
            return

        frame = self.cam_manager.read_frame()
        if frame is None:
            return

        # Dead pixels
        density = self.dead_slider.value() / 1000.0
        dead_map = np.random.rand(frame.shape[0], frame.shape[1]) < density

        # Эффекты
        frame = add_noise(frame)
        frame = jpeg_artifacts(frame, self.quality_slider.value())
        frame = simulate_dead_pixels(frame, dead_map)
        frame = rolling_shutter(frame, self.frame_idx * 0.03)
        frame = vignette(frame)
        frame = local_posterize(frame)

        # Превью
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        qimg = QtGui.QImage(frame_rgb.data, w, h, ch, QtGui.QImage.Format_RGB888)
        self.label.setPixmap(QtGui.QPixmap.fromImage(qimg))

        # Отправка в виртуальную камеру
        self.cam_manager.send_virtual(frame_rgb)

        self.frame_idx += 1
        self.timer.start(1000 // self.fps_slider.value())


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    gui = BadCamGUI()
    gui.show()
    sys.exit(app.exec())
