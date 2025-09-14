#!/usr/bin/env python3
# realistic_chinese_cam.py
# Реалистичная имитация дешёвой китайской веб-камеры (чтобы выглядело как настоящая, а не как эффект).
# Требования: python3, opencv-python, numpy, pyfakewebcam
# Установка:
#   pip install opencv-python numpy pyfakewebcam
# Запуск v4l2loopback (пример):
#   sudo modprobe v4l2loopback devices=1 video_nr=2 card_label="BadCam" exclusive_caps=1
# Запуск скрипта:
#   python3 realistic_chinese_cam.py --src 0 --vdev /dev/video2 --width 320 --height 240 --fps 10

import cv2
import numpy as np
import pyfakewebcam
import argparse
import time
import random
import math

# ---------------------------- Параметры ----------------------------
# Идея: оставить выходное разрешение низким (320x240 или 640x480),
# fps низкий (8-12) и добавить правдоподобные артефакты, которые меняются со временем.
DEFAULT_WIDTH = 320
DEFAULT_HEIGHT = 240
DEFAULT_FPS = 10

# ---------------------------- Утилиты эффектов ----------------------------
def make_vignette(w, h, strength=0.6):
    # маска виньетирования: центр ярче, края темнее
    X = np.linspace(-1, 1, w)
    Y = np.linspace(-1, 1, h)
    xx, yy = np.meshgrid(X, Y)
    circle = np.sqrt(xx**2 + yy**2)
    mask = 1.0 - (circle**2) * strength
    mask = np.clip(mask, 0.3, 1.0)
    return mask[..., None].astype(np.float32)

def add_shot_noise(img, scale=0.03):
    # shot noise — шум пропорционален яркости
    img_f = img.astype(np.float32) / 255.0
    # случайный фактор по яркости
    sigma = scale * (0.5 + img_f)
    noise = np.random.normal(0.0, 1.0, img.shape).astype(np.float32) * sigma
    out = img_f + noise
    out = np.clip(out, 0.0, 1.0)
    return (out * 255).astype(np.uint8)

def add_read_noise(img, sigma=6.0):
    # gaussian read noise
    noise = np.random.normal(0, sigma, img.shape).astype(np.int16)
    out = img.astype(np.int16) + noise
    out = np.clip(out, 0, 255).astype(np.uint8)
    return out

def simulate_dead_pixels(frame, dead_map):
    out = frame.copy()
    coords = np.argwhere(dead_map)  # теперь (y, x)
    if len(coords) == 0:
        return out
    random_colors = np.random.randint(0, 256, (len(coords), 3), dtype=np.uint8)
    for (y, x), color in zip(coords, random_colors):
        out[y, x] = color
    return out




def jpeg_compress_decompress(frame, quality=25, jitter=5):
    # небольшая рандомизация качества, чтобы не было одинаковых артефактов
    q = max(5, min(95, int(quality + random.uniform(-jitter, jitter))))
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), q]
    _, enc = cv2.imencode('.jpg', frame, encode_param)
    dec = cv2.imdecode(enc, cv2.IMREAD_COLOR)
    return dec

def chroma_shift(img, max_shift=2):
    # небольшое локальное смещение цветовых каналов (имитирует дешевую оптику)
    b,g,r = cv2.split(img)
    h,w = b.shape
    sx = random.randint(-max_shift, max_shift)
    sy = random.randint(-max_shift, max_shift)
    M = np.float32([[1,0,sx],[0,1,sy]])
    r2 = cv2.warpAffine(r, M, (w,h), borderMode=cv2.BORDER_REFLECT)
    sx = random.randint(-max_shift, max_shift)
    sy = random.randint(-max_shift, max_shift)
    M2 = np.float32([[1,0,sx],[0,1,sy]])
    b2 = cv2.warpAffine(b, M2, (w,h), borderMode=cv2.BORDER_REFLECT)
    return cv2.merge([b2,g,r2])

def rolling_shutter_effect(frame, motion_amount=2.0, phase=0.0):
    # смещение строк пропорционально вертикальной координате: простая имитация rolling shutter
    h,w = frame.shape[:2]
    out = np.zeros_like(frame)
    for y in range(h):
        shift = int(((y / h) - 0.5) * motion_amount + math.sin(phase + y*0.1) * (motion_amount*0.2))
        if shift > 0:
            out[y, shift:] = frame[y, :-shift]
            out[y, :shift] = frame[y, :1]  # replicate edge
        elif shift < 0:
            s = -shift
            out[y, :-s] = frame[y, s:]
            out[y, -s:] = frame[y, -1:]
        else:
            out[y] = frame[y]
    return out

def motion_blur_along_vector(frame, vx, vy, k=5):
    # простая motion blur: смазываем в направлении вектора (vx,vy)
    k = max(1, int(k))
    kernel = np.zeros((k, k), dtype=np.float32)
    # направим ядро вдоль вектора
    cx, cy = k//2, k//2
    for i in range(k):
        j = int(cx + (i - cx) * (vx if abs(vx) > 0.001 else 0.0))
        j = max(0, min(k-1, j))
        kernel[cy, i] = 1.0
    kernel /= kernel.sum() if kernel.sum() != 0 else 1.0
    out = cv2.filter2D(frame, -1, kernel)
    return out

def autoexposure_and_awb(frame, ae_gain, awb_gains):
    # ae_gain — масштаб яркости; awb_gains — tuple (b_gain,g_gain,r_gain)
    frame_f = frame.astype(np.float32)
    b,g,r = cv2.split(frame_f)
    b *= awb_gains[0]
    g *= awb_gains[1]
    r *= awb_gains[2]
    merged = cv2.merge([b,g,r])
    merged *= ae_gain
    merged = np.clip(merged, 0, 255).astype(np.uint8)
    return merged

# ---------------------------- Генератор карты "мёртвых пикселей" ----------------------------
def make_dead_pixel_map(w, h, density=0.0008):
    # density — доля пикселей с дефектом
    count = int(w * h * density)
    mask = np.zeros((h, w), dtype=bool)
    for _ in range(count):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        mask[y, x] = True
    return mask  # <-- только 2D маска


# ---------------------------- Основной класс ----------------------------
class RealisticCheapCam:
    def __init__(self, src=0, vdev='/dev/video2', width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, fps=DEFAULT_FPS):
        self.src = int(src)
        self.vdev = vdev
        self.W = width
        self.H = height
        self.fps = fps
        self.cap = cv2.VideoCapture(self.src)
        # пробуем задать параметры источника (иногда устройство игнорирует)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.W*2)   # брать побольше и потом масштабировать
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.H*2)
        self.cap.set(cv2.CAP_PROP_FPS, max(5, self.fps))
        self.fake = pyfakewebcam.FakeWebcam(self.vdev, self.W, self.H)
        self.prev_gray = None
        self.prev_frame = None
        self.frame_idx = 0
        self.vignette = make_vignette(self.W, self.H, strength=0.9)
        self.dead_map = make_dead_pixel_map(self.W, self.H, density=0.0006)
        # внутренние параметры которые медленно меняются (чтобы не было статичного "фильтра")
        self.awb_phase = random.random() * 10.0
        self.ae_phase = random.random() * 10.0
        self.jpeg_base_q = 24  # качество jpeg 〜 20-30 у убитых камер
        # небольшой набор "мерцания" от освещения (50/60Hz)
        self.mains_freq = 50.0 if random.random() < 0.5 else 60.0

    def run(self):
        interval = 1.0 / max(1, self.fps)
        while True:
            t0 = time.time()
            ret, frame = self.cap.read()
            if not ret:
                # если камера временно не даёт кадры
                time.sleep(0.05)
                continue

            # приводим к рабочему разрешению: уменьшаем сильно (имитация низкого сенсора)
            # но сначала применим небольшой случайный crop/шум для правдоподобности
            # случайный небольшой кадр (имитируем плохую автофокусировку/кроп)
            cx = random.randint(-4, 4)
            cy = random.randint(-4, 4)
            # безопасный ресайз
            try:
                frame = cv2.resize(frame, (self.W, self.H), interpolation=cv2.INTER_AREA)
            except Exception:
                frame = cv2.resize(frame, (self.W, self.H))

            # ----------------- Auto exposure (медленно меняется) -----------------
            self.ae_phase += 0.02 + random.uniform(-0.005, 0.01)
            ae_gain = 0.85 + 0.3 * math.sin(self.ae_phase) + random.uniform(-0.04, 0.04)
            # ----------------- AWB drift (медленно) -----------------
            self.awb_phase += 0.015 + random.uniform(-0.004, 0.008)
            b_gain = 0.9 + 0.2 * math.sin(self.awb_phase + 0.5)
            g_gain = 1.0 + 0.08 * math.sin(self.awb_phase + 1.1)
            r_gain = 0.85 + 0.18 * math.sin(self.awb_phase - 0.7)
            frame = autoexposure_and_awb(frame, ae_gain, (b_gain, g_gain, r_gain))

            # ----------------- Виньетка (центральная яркость лучше, края темнее) -----------------
            frame = (frame.astype(np.float32) * self.vignette).astype(np.uint8)

            # ----------------- Добавляем shot noise и read noise -----------------
            # shot noise сильнее в тёмных областях -> реалистично
            frame = add_shot_noise(frame, scale=0.045 + random.uniform(-0.01, 0.02))
            frame = add_read_noise(frame, sigma=4 + random.uniform(-1, 3))

            # ----------------- Небольшая хрома смещённость -----------------
            if random.random() < 0.7:
                frame = chroma_shift(frame, max_shift=1)

            # ----------------- Имитация rolling shutter (зависит от движения) -----------------
            # используем разницу между кадрами для оценки движения
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            motion_mag = 0.0
            if self.prev_frame is not None:
                diff = cv2.absdiff(gray, cv2.cvtColor(self.prev_frame, cv2.COLOR_BGR2GRAY))
                motion_mag = np.mean(diff) / 255.0  # 0..~0.5
            rs_amount = 1.0 + motion_mag * 6.0 + random.uniform(-0.5, 0.5)
            frame = rolling_shutter_effect(frame, motion_amount=rs_amount, phase=self.frame_idx * 0.03)

            # ----------------- Небольшое буферное смазывание при движении (ghost/jelly) -----------------
            if self.prev_frame is not None and motion_mag > 0.02:
                mix = min(0.35, 0.05 + motion_mag * 0.6)
                frame = cv2.addWeighted(frame, 1.0 - mix, self.prev_frame, mix, 0)

            # ----------------- Немного нерезкости в зависимости от освещённости -----------------
            # в темноте камеры бывают ещё гляже — симулируем
            mean_brightness = np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)) / 255.0
            blur_k = int(1 + (1.0 - mean_brightness) * 5)  # чем темнее — тем больше размытие
            if blur_k % 2 == 0: blur_k += 1
            if blur_k > 1:
                frame = cv2.GaussianBlur(frame, (blur_k, blur_k), 0)

            # ----------------- Случайные "глюки" экспозиции/баланса: пара кадров сильнее/светлее -----------------
            if random.random() < 0.01:
                # быстрый всплеск яркости/цвета
                spike_gain = 1.1 + random.uniform(0, 0.25)
                frame = np.clip(frame.astype(np.float32) * spike_gain, 0, 255).astype(np.uint8)

            # ----------------- JPEG compression artifacts (реалистично, с jitter) -----------------
            frame = jpeg_compress_decompress(frame, quality=self.jpeg_base_q, jitter=6)

            # ----------------- Мёртвые пиксели -----------------
            frame = simulate_dead_pixels(frame, self.dead_map)

            # ----------------- Слабая posterize / низкая цветовая глубина (но не слишком явная) -----------------
            levels = random.choice([32, 48, 64, 80])
            div = 256 // levels
            frame = (frame // div) * div

            # ----------------- 50/60Hz мерцание от ламп (особенно заметно при низком освещении) -----------------
            t = time.time()
            mains = 1.0 + 0.03 * math.sin(2 * math.pi * self.mains_freq * t + random.uniform(0, 2*math.pi))
            frame = np.clip(frame.astype(np.float32) * mains, 0, 255).astype(np.uint8)

            # ----------------- Небольшой кадро-дроп / лаг -----------------
            if random.random() < 0.03:
                # немного "подвисаем" (реалистично — сеть или камера)
                time.sleep(0.06 + random.uniform(0, 0.12))

            # ----------------- Уменьшаем насыщенность и добавляем лёгкий зелёный/синий оттенок -----------------
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[...,1] *= 0.85 + random.uniform(-0.05, 0.05)  # чуть меньше насыщение
            frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
            # лёгкий зелёный сдвиг
            frame = cv2.addWeighted(frame, 0.95, np.zeros_like(frame), 0.0, 0)
            # небольшой final chroma tint
            b,g,r = cv2.split(frame)
            g = cv2.addWeighted(g, 1.02, b, -0.02, 0)
            frame = cv2.merge([b,g,r])

            # Сохраняем текущий кадр для следующего шага
            self.prev_frame = frame.copy()
            self.frame_idx += 1

            # pyfakewebcam требует RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            try:
                self.fake.schedule_frame(rgb)
            except Exception as e:
                print("Ошибка записи в виртуальное устройство:", e)
                break

            # синхронизация по fps
            dt = time.time() - t0
            sleep = interval - dt
            if sleep > 0:
                time.sleep(sleep)

# ---------------------------- CLI и запуск ----------------------------
def main():
    p = argparse.ArgumentParser(description="Realistic cheap Chinese cam emulator (v4l2loopback)")
    p.add_argument('--src', default=0, help='источник (индекс камеры или путь)')
    p.add_argument('--vdev', default='/dev/video2', help='виртуальное устройство v4l2loopback')
    p.add_argument('--width', type=int, default=DEFAULT_WIDTH)
    p.add_argument('--height', type=int, default=DEFAULT_HEIGHT)
    p.add_argument('--fps', type=int, default=DEFAULT_FPS)
    args = p.parse_args()

    print("Запуск realistic_chinese_cam: src=%s vdev=%s %dx%d@%dfps" % (args.src, args.vdev, args.width, args.height, args.fps))
    cam = RealisticCheapCam(src=args.src, vdev=args.vdev, width=args.width, height=args.height, fps=args.fps)
    cam.run()

if __name__ == '__main__':
    main()
