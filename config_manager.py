import json
import os

CONFIG_PATH = "/home/pi/pipi_terminal/config.json"

def load_settings():
    """Загружает настройки из JSON. Если файла нет, возвращает дефолт"""
    defaults = {
        "alarm_time": "07:00",
        "alarm_enabled": True,
        "alarm_station_idx": 1,
        "alarm_sound_type": "radio",
        "news_feed_url": "https://reddit.com",
        "matrix_speed_factor": 1.0
    }
    if not os.path.exists(CONFIG_PATH):
        return defaults
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return defaults

def save_settings(settings):
    """Сохраняет измененные переменные обратно в файл"""
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception:
        return False
