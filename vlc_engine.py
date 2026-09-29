import subprocess
import pygame

# Модуль управления фоновым аудиовещанием через VLC HTTP API
# Хранит полный список радиостанций и контролирует их состояние

STATIONS = [
    {"name": "Main Station (All Fallout OST)", "url": "https://fallout.fm:8444/falloutfm1.ogg"},
    {"name": "Galaxy News Radio (Fallout 3)", "url": "https://fallout.fm:8444/falloutfm2.ogg"},
    {"name": "Radio New Vegas (Fallout NV)", "url": "https://fallout.fm:8444/falloutfm3.ogg"},
    {"name": "Fallout 2 (Original OST)", "url": "https://fallout.fm:8444/falloutfm4.ogg"},
    {"name": "Fallout 1 (Original OST)", "url": "https://fallout.fm:8444/falloutfm5.ogg"},
    {"name": "Diamond City Radio (Fallout 4)", "url": "https://fallout.fm:8444/falloutfm6.ogg"},
    {"name": "Fallout 4 Classical Radio", "url": "https://fallout.fm:8444/falloutfm7.ogg"},
    {"name": "Fallout 4 (MWTCF)", "url": "https://fallout.fm:8444/falloutfm8.ogg"},
    {"name": "Fallout 76 (Classical)", "url": "https://fallout.fm:8444/falloutfm9.ogg"},
    {"name": "Fallout 76 (General)", "url": "https://fallout.fm:8444/falloutfm10.ogg"}
]

mplayer_process = None

def init_vlc(start_idx, volume):
    """Первичная инициализация плеера при старте операционной системы"""
    play_station(start_idx, volume)

def run_vlc_cmd(command, val=None):
    """Отправка быстрых фоновых запросов в HTTP-интерфейс VLC"""
    url = f"http://localhost:8080/requests/status.xml?command={command}"
    if val is not None:
        url += f"&val={val}"
    cmd = f"curl -s -u :SovIntel '{url}'"
    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def play_station(idx, current_volume):
    """Запуск выбранного потока ogg с очисткой старых фоновых процессов"""
    global mplayer_process
    stop_audio()
    full_url = STATIONS[idx]["url"]
    try:
        mplayer_process = subprocess.Popen(
            ["cvlc", "--intf", "http", "--http-password", "SovIntel", "--http-port", "8080", "--network-caching=500", full_url],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        # Пауза, чтобы локальный веб-сервер VLC успел подняться в памяти малинки
        pygame.time.wait(1000)
        set_volume(current_volume)
    except Exception:
        pass

def set_volume(val):
    """Синхронизация шкалы громкости Pygame (0-100) с параметрами VLC (0-256)"""
    vlc_vol = int((val / 100) * 256)
    run_vlc_cmd("volume", vlc_vol)

def stop_audio():
    """Полное уничтожение фонового процесса вещания"""
    global mplayer_process
    if mplayer_process:
        try:
            mplayer_process.kill()
        except Exception:
            pass
        mplayer_process = None
