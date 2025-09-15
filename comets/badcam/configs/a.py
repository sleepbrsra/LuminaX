import cv2
import numpy as np
import subprocess

# Настройки "2$ камеры"
WIDTH, HEIGHT, FPS = 320, 240, 10

# Запуск ffmpeg для записи в виртуальную камеру
ffmpeg = subprocess.Popen([
    "ffmpeg",
    "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-pix_fmt", "bgr24",
    "-s", f"{WIDTH}x{HEIGHT}",
    "-r", str(FPS),
    "-i", "-",                     # stdin
    "-f", "v4l2",
    "-pix_fmt", "yuv420p",
    f"/dev/video2"                 # твоя виртуальная камера
], stdin=subprocess.PIPE)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # уменьшаем разрешение
    frame = cv2.resize(frame, (WIDTH, HEIGHT))

    # искусственное ухудшение: шум, сжатие, размытость
    frame = cv2.GaussianBlur(frame, (3, 3), 0)  # мыльно
    noise = np.random.randint(0, 50, frame.shape, dtype=np.uint8)
    frame = cv2.add(frame, noise)               # шум
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 25]
    _, enc = cv2.imencode('.jpg', frame, encode_param)
    frame = cv2.imdecode(enc, 1)                # артефакты JPEG

    # отправка кадра в ffmpeg
    ffmpeg.stdin.write(frame.tobytes())
