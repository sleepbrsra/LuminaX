#!/usr/bin/env python3
"""
bad_cam_harder.py
Агрeссивное ухудшение камеры и вывод в виртуальное устройство /dev/videoX (v4l2loopback).
Требования: opencv-python, numpy, pyfakewebcam
Запуск: sudo modprobe v4l2loopback devices=1 video_nr=2 card_label="BadCam"
       python3 bad_cam_harder.py --preset nightmare
"""

import cv2
import numpy as np
import pyfakewebcam
import argparse
import time
import random

# --- utils эффектов ---
def jpeg_artifacts(frame, quality=10):
    # Добавляет артефакты сжатия JPEG
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
    _, enc = cv2.imencode('.jpg', frame, encode_param)
    dec = cv2.imdecode(enc, cv2.IMREAD_COLOR)
    return dec

def chroma_subsample(frame, factor=2):
    # Downsample chroma channels (YCrCb) — теряется цвет
    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)
    # уменьшение разрешения Cr/Cb и восстановление -> потеря цветовой детализации
    small_cr = cv2.resize(cr, (cr.shape[1]//factor, cr.shape[0]//factor), interpolation=cv2.INTER_LINEAR)
    small_cb = cv2.resize(cb, (cb.shape[1]//factor, cb.shape[0]//factor), interpolation=cv2.INTER_LINEAR)
    cr_up = cv2.resize(small_cr, (cr.shape[1], cr.shape[0]), interpolation=cv2.INTER_NEAREST)
    cb_up = cv2.resize(small_cb, (cb.shape[1], cb.shape[0]), interpolation=cv2.INTER_NEAREST)
    merged = cv2.merge([y, cr_up, cb_up])
    return cv2.cvtColor(merged, cv2.COLOR_YCrCb2BGR)

def posterize(frame, levels=8):
    # Уменьшение глубины цвета
    div = 256 // max(1, levels)
    return (frame // div) * div

def add_scanlines(frame, strength=0.2, period=2):
    # Темные горизонтальные полосы
    out = frame.copy().astype(np.float32)
    h = out.shape[0]
    for i in range(0, h, period*2):
        out[i:i+period,:,:] *= (1.0 - strength)
    out = np.clip(out, 0, 255).astype(np.uint8)
    return out

def add_block_noise(frame, blocks=20, max_size=80):
    out = frame.copy()
    h,w = out.shape[:2]
    for _ in range(blocks):
        bw = random.randint(8, max_size)
        bh = random.randint(8, max_size)
        x = random.randint(0, max(0, w-bw))
        y = random.randint(0, max(0, h-bh))
        color = np.random.randint(0,256, (3,), dtype=np.uint8)
        out[y:y+bh, x:x+bw] = color
    return out

def temporal_jitter(prev, curr, mix=0.5):
    # смешивание с предыдущим кадром (эффект «смазывания/ghost»)
    return cv2.addWeighted(curr, 1.0-mix, prev, mix, 0)

# --- основной loop ---
class BadCamHard:
    def __init__(self, src=0, vdev='/dev/video2', width=640, height=480, fps=10, preset='bad'):
        self.src = int(src)
        self.vdev = vdev
        self.W = width
        self.H = height
        self.fps = fps
        self.cap = cv2.VideoCapture(self.src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.H)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.fake = pyfakewebcam.FakeWebcam(self.vdev, self.W, self.H)
        self.prev_frame = None
        self.cfg = self._preset_cfg(preset)

    def _preset_cfg(self, preset):
        # пресеты: от 'bad' до 'nightmare'
        presets = {
            'bad': {
                'down_res': (160,120), 'pixelate_scale':4, 'blur':5, 'noise':20,
                'jpeg_q':30, 'chroma':1, 'poster':32, 'scanlines':0.06,
                'blocks':4, 'frame_drop':0.02, 'freeze_chance':0.005, 'temporal_mix':0.06
            },
            'awful': {
                'down_res': (120,90), 'pixelate_scale':6, 'blur':9, 'noise':35,
                'jpeg_q':15, 'chroma':2, 'poster':16, 'scanlines':0.12,
                'blocks':8, 'frame_drop':0.06, 'freeze_chance':0.02, 'temporal_mix':0.14
            },
            'horrible': {
                'down_res': (80,60), 'pixelate_scale':8, 'blur':13, 'noise':55,
                'jpeg_q':8, 'chroma':3, 'poster':8, 'scanlines':0.18,
                'blocks':14, 'frame_drop':0.15, 'freeze_chance':0.06, 'temporal_mix':0.28
            },
            'nightmare': {
                'down_res': (40,30), 'pixelate_scale':16, 'blur':21, 'noise':90,
                'jpeg_q':4, 'chroma':4, 'poster':4, 'scanlines':0.28,
                'blocks':28, 'frame_drop':0.35, 'freeze_chance':0.18, 'temporal_mix':0.45
            }
        }
        return presets.get(preset, presets['horrible'])

    def run(self):
        interval = 1.0 / max(1, self.fps)
        frozen_frame = None
        freeze_until = 0
        while True:
            t0 = time.time()
            # симулируем выпадение кадра
            if random.random() < self.cfg['frame_drop']:
                # пропуск отправки кадра (пауза)
                time.sleep(interval)
                continue

            # случайная заморозка кадра
            if time.time() < freeze_until and frozen_frame is not None:
                frame = frozen_frame.copy()
            else:
                ret, frame = self.cap.read()
                if not ret:
                    # если нет кадра — пауза и повтор
                    time.sleep(0.05)
                    continue

                # шанс инициировать заморозку
                if random.random() < self.cfg['freeze_chance']:
                    frozen_frame = frame.copy()
                    freeze_time = random.uniform(0.2, 2.5)  # сколько держать
                    freeze_until = time.time() + freeze_time

            # сильное уменьшение разрешения → пикселизация
            dw, dh = self.cfg['down_res']
            frame = cv2.resize(frame, (dw, dh), interpolation=cv2.INTER_LINEAR)
            frame = cv2.resize(frame, (self.W, self.H), interpolation=cv2.INTER_NEAREST)

            # геометрический джиттер: небольшое смещение кадра
            max_shift = max(1, int(min(self.W, self.H) * 0.03))
            dx = random.randint(-max_shift, max_shift)
            dy = random.randint(-max_shift, max_shift)
            M = np.float32([[1,0,dx],[0,1,dy]])
            frame = cv2.warpAffine(frame, M, (self.W, self.H), borderMode=cv2.BORDER_REPLICATE)

            # сильное размытие
            k = self.cfg['blur']
            if k % 2 == 0: k += 1
            if k > 1:
                frame = cv2.GaussianBlur(frame, (k, k), 0)

            # posterize / уменьшение глубины цвета
            frame = posterize(frame, levels=self.cfg['poster'])

            # хрома сабсемплинг (плохая цветопередача)
            if self.cfg['chroma'] > 1:
                frame = chroma_subsample(frame, factor=self.cfg['chroma'])

            # шум
            if self.cfg['noise'] > 0:
                noise = np.random.normal(0, self.cfg['noise'], frame.shape).astype(np.float32)
                frame = np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)

            # блоковые искажения
            if self.cfg['blocks'] > 0:
                frame = add_block_noise(frame, blocks=self.cfg['blocks'], max_size=max(16, self.W//8))

            # JPEG артефакты
            frame = jpeg_artifacts(frame, quality=self.cfg['jpeg_q'])

            # scanlines
            frame = add_scanlines(frame, strength=self.cfg['scanlines'], period=2)

            # temporal (ghost) — смешивание с предыдущим кадром
            if self.prev_frame is not None and self.cfg['temporal_mix'] > 0:
                frame = temporal_jitter(self.prev_frame, frame, mix=self.cfg['temporal_mix'])

            self.prev_frame = frame.copy()

            # в pyfakewebcam нужен RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            try:
                self.fake.schedule_frame(rgb)
            except Exception as e:
                print("Ошибка записи в виртуальное устройство:", e)
                break

            # синхронизация fps
            dt = time.time() - t0
            sleep = interval - dt
            if sleep > 0:
                time.sleep(sleep)


# --- CLI ---
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--src', default=0, help='источник камеры (индекс или путь)')
    p.add_argument('--vdev', default='/dev/video2', help='виртуальное устройство (v4l2loopback)')
    p.add_argument('--width', type=int, default=640)
    p.add_argument('--height', type=int, default=480)
    p.add_argument('--fps', type=int, default=10)
    p.add_argument('--preset', choices=['bad','awful','horrible','nightmare'], default='horrible')
    args = p.parse_args()

    print("Запуск: src=%s vdev=%s %dx%d@%dfps preset=%s" % (args.src, args.vdev, args.width, args.height, args.fps, args.preset))
    bc = BadCamHard(src=args.src, vdev=args.vdev, width=args.width, height=args.height, fps=args.fps, preset=args.preset)
    bc.run()

if __name__ == '__main__':
    main()
