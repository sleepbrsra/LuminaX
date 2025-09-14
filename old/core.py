# core.py
import cv2
import numpy as np
import random
import math

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
