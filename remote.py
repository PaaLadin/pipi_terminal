import os
import glob
import time
from evdev import InputDevice

class RemoteListener:
    def __init__(self):
        self.device = None
        self.last_reconnect_time = 0
        self.try_reconnect()

    def try_reconnect(self):
        """Пытается динамически найти и открыть пульт в системе"""
        now = time.time()
        if now - self.last_reconnect_time < 3.0:  # Защита от спама ядра
            return
        self.last_reconnect_time = now
        
        target_path = None
        # Ищем строго Consumer Control
        for path in glob.glob('/dev/input/event*'):
            try:
                dev = InputDevice(path)
                if "Consumer Control" in dev.name:
                    target_path = path
                    self.device = dev
                    break
            except:
                pass

        if not self.device:
            for path in glob.glob('/dev/input/event*'):
                try:
                    dev = InputDevice(path)
                    if "remote" in dev.name.lower():
                        target_path = path
                        self.device = dev
                        break
                except:
                    pass

        if self.device:
            print(f"ПОДКЛЮЧЕН ПУЛЬТ: {target_path} ({self.device.name})")

    def poll_keys(self):
        """Прямой неблокирующий опрос кнопок с автоподключением"""
        if not self.device:
            self.try_reconnect()
            return None
        try:
            for event in self.device.read():
                if event.type == 1 and event.value == 1: # EV_KEY, Нажатие
                    return event.code
        except BlockingIOError:
            pass
        except Exception:
            # Если пульт отвалился (уснул или пропал из systemd), сбрасываем устройство
            self.device = None
        return None
