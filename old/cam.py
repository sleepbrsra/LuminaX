# cam.py
import cv2
import sys

class CameraManager:
    def __init__(self, platform=None):
        self.platform = platform or sys.platform
        self.cap = None

    def list_cameras(self, max_devices=10):
        """Возвращает список индексов доступных камер"""
        available = []
        for i in range(max_devices):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(str(i))
                cap.release()
        return available

    def open_camera(self, index):
        self.cap = cv2.VideoCapture(int(index))
        if not self.cap.isOpened():
            self.cap = None
            raise RuntimeError(f"Cannot open camera {index}")

    def read_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None

    def send_virtual(self, frame):
        # Заглушка: здесь будет код для v4l2loopback или OBS VirtualCam
        pass

    def close(self):
        if self.cap:
            self.cap.release()
            self.cap = None
