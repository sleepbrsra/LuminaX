#!/usr/bin/env python3
# bad_cam_gui_crossplatform.py
import sys, time, random, math
import numpy as np
import cv2
from PySide6 import QtCore, QtWidgets, QtGui

try:
    import pyvirtualcam
    VIRTUALCAM_AVAILABLE = True
except ImportError:
    VIRTUALCAM_AVAILABLE = False
    print("pyvirtualcam не найдено, вывод в виртуальную камеру отключен")

# ----------------- Эффекты -----------------
def add_noise(frame, scale=0.05, read_sigma=5):
    img_f = frame.astype(np.float32)/255.0
    sigma = scale*(0.5+img_f)
    noise = np.random.normal(0,1,frame.shape).astype(np.float32)*sigma
    frame = np.clip(img_f+noise,0,1)*255
    rn = np.random.normal(0,read_sigma,frame.shape)
    frame = np.clip(frame+rn,0,255).astype(np.uint8)
    return frame

def jpeg_artifacts(frame, quality=18):
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, enc = cv2.imencode('.jpg', frame, encode_param)
    return cv2.imdecode(enc, cv2.IMREAD_COLOR)

def simulate_dead_pixels(frame, dead_map):
    out = frame.copy()
    coords = np.argwhere(dead_map)
    colors = np.random.randint(0,256,(len(coords),3),dtype=np.uint8)
    for (y,x), color in zip(coords,colors):
        out[y,x] = color
    return out

def rolling_shutter(frame, phase, motion_amount=2.0):
    h,w = frame.shape[:2]
    out = np.zeros_like(frame)
    for y in range(h):
        shift = int(((y/h)-0.5)*motion_amount + math.sin(phase+y*0.1)*(motion_amount*0.3))
        if shift>0:
            out[y,shift:] = frame[y,:-shift]
            out[y,:shift] = frame[y,0:1]
        elif shift<0:
            s=-shift
            out[y,:-s] = frame[y,s:]
            out[y,-s:] = frame[y,-1:]
        else:
            out[y] = frame[y]
    return out

def vignette(frame):
    h,w = frame.shape[:2]
    X = np.linspace(-1,1,w)
    Y = np.linspace(-1,1,h)
    xx,yy = np.meshgrid(X,Y)
    mask = 1.0-(xx**2+yy**2)*0.9
    mask = np.clip(mask,0.3,1.0)
    return (frame.astype(np.float32)*mask[...,None]).astype(np.uint8)

def local_posterize(frame):
    levels = random.choice([32,48,64])
    div = 256//levels
    return (frame//div)*div

# ----------------- GUI -----------------
class BadCamGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultra Bad Chinese Cam GUI")
        self.resize(480,700)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.cap = None
        self.running = False
        self.frame_idx = 0
        self.virtual_cam = None

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # ----------------- Выбор платформы -----------------
        self.platform_combo = QtWidgets.QComboBox()
        self.platform_combo.addItems(["Windows","Linux"])
        layout.addWidget(QtWidgets.QLabel("Выберите платформу"))
        layout.addWidget(self.platform_combo)

        # Камера
        self.cam_combo = QtWidgets.QComboBox()
        self.cam_combo.addItems([str(i) for i in range(5)])
        layout.addWidget(QtWidgets.QLabel("Выберите камеру"))
        layout.addWidget(self.cam_combo)

        # FPS
        self.fps_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.fps_slider.setRange(1,30)
        self.fps_slider.setValue(10)
        layout.addWidget(QtWidgets.QLabel("FPS"))
        layout.addWidget(self.fps_slider)

        # JPEG
        self.quality_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.quality_slider.setRange(5,50)
        self.quality_slider.setValue(18)
        layout.addWidget(QtWidgets.QLabel("JPEG качество"))
        layout.addWidget(self.quality_slider)

        # Dead pixels
        self.dead_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.dead_slider.setRange(0,1000)
        self.dead_slider.setValue(2)
        layout.addWidget(QtWidgets.QLabel("Dead pixels density"))
        layout.addWidget(self.dead_slider)

        # Кнопка старт/стоп
        self.start_btn = QtWidgets.QPushButton("Старт")
        self.start_btn.clicked.connect(self.toggle)
        layout.addWidget(self.start_btn)

        # Превью
        self.label = QtWidgets.QLabel()
        self.label.setFixedSize(320,240)
        layout.addWidget(self.label)

    def toggle(self):
        if not self.running:
            cam_idx = int(self.cam_combo.currentText())
            self.cap = cv2.VideoCapture(cam_idx)
            self.running = True
            self.dead_map = np.zeros((240,320),dtype=bool)
            self.timer.start(1000//self.fps_slider.value())
            self.start_btn.setText("Стоп")

            # Виртуальная камера
            platform = self.platform_combo.currentText()
            if VIRTUALCAM_AVAILABLE:
                if platform=="Windows":
                    self.virtual_cam = pyvirtualcam.Camera(width=320,height=240,fps=self.fps_slider.value(),backend=pyvirtualcam.Backend.OBS)
                elif platform=="Linux":
                    self.virtual_cam = pyvirtualcam.Camera(width=320,height=240,fps=self.fps_slider.value())
        else:
            self.running = False
            self.timer.stop()
            if self.cap: self.cap.release()
            if self.virtual_cam: self.virtual_cam.close()
            self.start_btn.setText("Старт")

    def update_frame(self):
        if not self.running or self.cap is None:
            return
        ret, frame = self.cap.read()
        if not ret: return
        frame = cv2.resize(frame,(320,240),interpolation=cv2.INTER_AREA)

        # Dead pixels
        density = self.dead_slider.value()/1000.0
        self.dead_map = np.random.rand(240,320) < density

        # Применяем эффекты
        frame = add_noise(frame)
        frame = jpeg_artifacts(frame,self.quality_slider.value())
        frame = simulate_dead_pixels(frame,self.dead_map)
        frame = rolling_shutter(frame,self.frame_idx*0.03)
        frame = vignette(frame)
        frame = local_posterize(frame)

        # Показ в GUI
        frame_rgb = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        h,w,ch = frame_rgb.shape
        qimg = QtGui.QImage(frame_rgb.data,w,h,ch,QtGui.QImage.Format_RGB888)
        self.label.setPixmap(QtGui.QPixmap.fromImage(qimg))

        # Отправка в виртуальную камеру
        if self.virtual_cam:
            self.virtual_cam.send(frame_rgb)
            self.virtual_cam.sleep_until_next_frame()

        self.frame_idx +=1
        self.timer.start(1000//self.fps_slider.value())

# ----------------- Запуск -----------------
if __name__=="__main__":
    app = QtWidgets.QApplication(sys.argv)
    gui = BadCamGUI()
    gui.show()
    sys.exit(app.exec())
