#!/usr/bin/env python3
"""
Super Realistic Bad Chinese Cam
- Linux only (v4l2loopback)
- Реалистичная имитация дешевой веб-камеры
- Требования: python3, opencv-python, numpy
- Установка:
    pip install opencv-python numpy
- Запуск v4l2loopback:
    sudo modprobe v4l2loopback devices=1 video_nr=2 card_label="FakeCam" max_buffers=2
- Запуск скрипта:
    python3 super_bad_chinese_cam.py
"""

import cv2
import numpy as np
import subprocess
import time
import random
import math

# ----------------- Настройки -----------------
WIDTH, HEIGHT, FPS = 320, 240, 10
VDEV = "/dev/video2"
JPEG_QUALITY = 18
DEAD_PIXEL_DENSITY = 0.001  # чуть выше, хаотично

# ----------------- Генераторы эффектов -----------------
def make_dead_pixel_map(w,h,density=0.001):
    mask = np.zeros((h,w),dtype=bool)
    count = max(1,int(w*h*density))
    for _ in range(count):
        x = random.randint(0,w-1)
        y = random.randint(0,h-1)
        mask[y,x] = True
    return mask

def simulate_dead_pixels(frame, dead_map):
    out = frame.copy()
    coords = np.argwhere(dead_map)
    colors = np.random.randint(0,256,(len(coords),3),dtype=np.uint8)
    for (y,x), color in zip(coords,colors):
        out[y,x] = color
    return out

def add_noise(frame, scale=0.05, read_sigma=5):
    img_f = frame.astype(np.float32)/255.0
    sigma = scale*(0.5+img_f)
    noise = np.random.normal(0,1,frame.shape).astype(np.float32)*sigma
    frame = np.clip(img_f + noise,0,1)*255
    rn = np.random.normal(0,read_sigma,frame.shape)
    frame = np.clip(frame+rn,0,255).astype(np.uint8)
    return frame

def jpeg_artifacts(frame, quality=18):
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, enc = cv2.imencode('.jpg',frame,encode_param)
    return cv2.imdecode(enc,cv2.IMREAD_COLOR)

def chroma_shift(img,max_shift=1):
    b,g,r = cv2.split(img)
    h,w = b.shape
    for ch in [b,r]:
        sx = random.randint(-max_shift,max_shift)
        sy = random.randint(-max_shift,max_shift)
        M = np.float32([[1,0,sx],[0,1,sy]])
        ch[:] = cv2.warpAffine(ch,(w,h),M, borderMode=cv2.BORDER_REFLECT)
    return cv2.merge([b,g,r])

def rolling_shutter(frame,phase,motion_amount=2.0):
    h,w = frame.shape[:2]
    out = np.zeros_like(frame)
    for y in range(h):
        shift = int(((y/h)-0.5)*motion_amount + math.sin(phase+y*0.1)*(motion_amount*0.3))
        if shift>0:
            out[y,shift:] = frame[y,:-shift]
            out[y,:shift] = frame[y,0:1]
        elif shift<0:
            s = -shift
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
    block = 4
    for y in range(0,frame.shape[0],block):
        for x in range(0,frame.shape[1],block):
            patch = frame[y:y+block,x:x+block]
            div = 256//levels
            frame[y:y+block,x:x+block] = (patch//div)*div
    return frame

def awb_exposure(frame,ae_phase,awb_phase):
    b,g,r = cv2.split(frame.astype(np.float32))
    ae_gain = 0.85 + 0.3*math.sin(ae_phase)
    b_gain = 0.9 + 0.2*math.sin(awb_phase+0.5)
    g_gain = 1.0 + 0.08*math.sin(awb_phase+1.1)
    r_gain = 0.85 + 0.18*math.sin(awb_phase-0.7)
    b*=b_gain*ae_gain
    g*=g_gain*ae_gain
    r*=r_gain*ae_gain
    return cv2.merge([b,g,r]).astype(np.uint8)

# ----------------- Запуск ffmpeg -----------------
ffmpeg = subprocess.Popen([
    "ffmpeg",
    "-y",
    "-f","rawvideo",
    "-vcodec","rawvideo",
    "-pix_fmt","bgr24",
    "-s", f"{WIDTH}x{HEIGHT}",
    "-r", str(FPS),
    "-i","-",
    "-f","v4l2",
    "-pix_fmt","yuv420p",
    VDEV
], stdin=subprocess.PIPE)

# ----------------- Основной цикл -----------------
cap = cv2.VideoCapture(0)
dead_map = make_dead_pixel_map(WIDTH,HEIGHT,DEAD_PIXEL_DENSITY)
prev_frame = None
frame_idx = 0
ae_phase = random.random()*10
awb_phase = random.random()*10
mains_freq = 50 if random.random()<0.5 else 60

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue

        frame = cv2.resize(frame,(WIDTH,HEIGHT),interpolation=cv2.INTER_AREA)

        # экспозиция/AWB
        ae_phase+=0.02+random.uniform(-0.005,0.01)
        awb_phase+=0.015+random.uniform(-0.004,0.008)
        frame = awb_exposure(frame,ae_phase,awb_phase)

        # эффекты
        frame = vignette(frame)
        frame = add_noise(frame)
        frame = chroma_shift(frame)
        frame = rolling_shutter(frame,frame_idx*0.03,motion_amount=1.5)
        frame = jpeg_artifacts(frame,JPEG_QUALITY)
        frame = simulate_dead_pixels(frame,dead_map)
        frame = local_posterize(frame)

        # мерцание ламп
        t = time.time()
        mains = 1.0 + 0.03*math.sin(2*math.pi*mains_freq*t + random.uniform(0,2*math.pi))
        frame = np.clip(frame.astype(np.float32)*mains,0,255).astype(np.uint8)

        # случайное «подвисание» кадра
        if random.random()<0.03:
            time.sleep(0.06+random.uniform(0,0.12))

        # отправка в виртуалку
        ffmpeg.stdin.write(frame.tobytes())
        frame_idx+=1

finally:
    cap.release()
    ffmpeg.stdin.close()
    ffmpeg.wait()
