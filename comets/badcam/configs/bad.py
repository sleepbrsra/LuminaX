import cv2
import numpy as np
import pyfakewebcam
import random
import time

# Настройки
CAMERA_SRC = 0
VIRTUAL_DEV = "/dev/video2"
WIDTH, HEIGHT = 640, 480
FPS = 10   # китайские камеры редко тянут выше 10–15 fps

# открыть реальную камеру
cap = cv2.VideoCapture(CAMERA_SRC)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

# виртуальная камера
cam = pyfakewebcam.FakeWebcam(VIRTUAL_DEV, WIDTH, HEIGHT)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # ↓ ЭФФЕКТЫ ДЕШЁВОЙ КАМЕРЫ ↓

    # снизить резкость (имитация мыльной линзы)
    frame = cv2.GaussianBlur(frame, (9, 9), 2)

    # пикселизация
    small = cv2.resize(frame, (80, 60), interpolation=cv2.INTER_LINEAR)
    frame = cv2.resize(small, (WIDTH, HEIGHT), interpolation=cv2.INTER_NEAREST)

    # шум (как от дешёвой матрицы)
    noise = np.random.normal(0, 50, frame.shape).astype(np.int16)
    frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # плохая цветопередача (смещаем баланс белого)
    b, g, r = cv2.split(frame)
    g = cv2.addWeighted(g, 1.2, r, -0.1, 0)   # зелёный перебор
    r = cv2.addWeighted(r, 0.8, b, 0.2, 0)    # красный уходит в синеву
    frame = cv2.merge([b, g, r])

    # редкие "фризы" (заставляем кадр повторяться)
    if random.random() < 0.05:  
        time.sleep(0.2)  # подвисание на 200 мс

    # RGB для виртуальной камеры
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # отдать кадр
    cam.schedule_frame(frame)

    # снизим FPS
    time.sleep(1 / FPS)
