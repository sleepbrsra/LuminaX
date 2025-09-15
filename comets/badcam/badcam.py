import importlib
import os
import subprocess

class BadCam:
    def __init__(self):
        self.enabled = False
        self.loopback_enabled = False
        self.current_config = None
        self.modprobe_name = "BadCam"
        self.video_nr = 2  # виртуальная камера /dev/video2

    def list_configs(self):
        """Показать все доступные конфиги"""
        configs_path = os.path.join(os.path.dirname(__file__), "configs")
        return [f[:-3] for f in os.listdir(configs_path) if f.endswith(".py")]

    def set_config(self, config_name: str):
        """Загрузить конфиг (a.py, b.py и т.д.)"""
        try:
            module = importlib.import_module(f"comets.badcam.configs.{config_name}")
            self.current_config = module
            print(f"[BadCam] Загружен конфиг: {config_name}")
        except ModuleNotFoundError:
            print(f"[BadCam] Конфиг {config_name} не найден!")

    def set_modprobe_name(self, name: str):
        """Изменить название устройства"""
        self.modprobe_name = name
        print(f"[BadCam] card_label установлен: {name}")

    def enable_loopback(self):
        """Включить виртуальную вебку"""
        if self.loopback_enabled:
            print("[BadCam] Loopback уже включён")
            return

        cmd = [
            "sudo", "modprobe", "v4l2loopback",
            f"devices=1",
            f"video_nr={self.video_nr}",
            f'card_label="{self.modprobe_name}"',
            "exclusive_caps=1"
        ]
        try:
            subprocess.run(" ".join(cmd), shell=True, check=True)
            self.loopback_enabled = True
            print(f"[BadCam] Виртуальная камера запущена: /dev/video{self.video_nr}")
        except subprocess.CalledProcessError as e:
            print(f"[BadCam] Ошибка запуска loopback: {e}")

    def disable_loopback(self):
        """Выключить виртуальную вебку"""
        if not self.loopback_enabled:
            print("[BadCam] Loopback уже выключен")
            return

        try:
            subprocess.run("sudo modprobe -r v4l2loopback", shell=True, check=True)
            self.loopback_enabled = False
            print("[BadCam] Виртуальная камера выключена")
        except subprocess.CalledProcessError as e:
            print(f"[BadCam] Ошибка отключения loopback: {e}")

    def enable(self):
        """Включить BadCam"""
        if not self.current_config:
            print("[BadCam] Сначала выбери конфиг!")
            return
        if not self.loopback_enabled:
            print("[BadCam] Виртуальная камера выключена!")
            return

        self.enabled = True
        print(f"[BadCam] Комета запущена ({self.modprobe_name})")

    def disable(self):
        """Выключить BadCam"""
        self.enabled = False
        print("[BadCam] Комета выключена")
