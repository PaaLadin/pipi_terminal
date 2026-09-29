# ====================================================================
# SovIntel OS ENERGY & SLEEP ARCHITECTURE MANAGEMENT DAEMON
# ====================================================================
import os
import subprocess
import math
import pygame
from datetime import datetime

DEEP_SLEEP_FILE = "/home/pi/pipi_terminal/.deep_sleep"

def update_energy_state(now, inactivity_sec, active_tab, nav_focus, manual_cap, current_vol, is_muted):
    """Расчет состояний активности терминала на основе таймстампов"""
    dt_now = datetime.now()
    is_daytime = (7 <= dt_now.hour < 23)

    new_tab = active_tab
    new_focus = nav_focus
    dim_factor = 1.0
    new_mute = is_muted
    target_volume = current_vol

    if nav_focus in ('content', 'tabs', 'settings_main', 'settings_sub'):
        if active_tab == 5 and inactivity_sec >= 300:
            new_tab = 2 if is_daytime else 0
            new_focus = 'content'
        elif active_tab in (3, 4) and inactivity_sec >= 600:
            new_tab = 2 if is_daytime else 0
            new_focus = 'content'

    if new_tab in (0, 2):
        if inactivity_sec < 300: dim_factor = 1.0
        elif inactivity_sec < 600: dim_factor = 0.75
        elif inactivity_sec < 900: dim_factor = 0.50
        elif inactivity_sec < 1200: dim_factor = 0.25
        else:
            if not is_daytime:
                dim_factor = 0.05
                new_mute = True
                if not os.path.exists(DEEP_SLEEP_FILE):
                    with open(DEEP_SLEEP_FILE, "w") as f: f.write("1")
            else:
                dim_factor = 0.25
    else:
        dim_factor = 1.0
        target_volume = manual_cap
        if os.path.exists(DEEP_SLEEP_FILE):
            try: os.remove(DEEP_SLEEP_FILE)
            except: pass

    if new_tab in (0, 2) and not new_mute:
        calculated_vol = int(manual_cap * dim_factor)
        if calculated_vol < current_vol: target_volume = calculated_vol

    return new_tab, new_focus, dim_factor, target_volume, new_mute

def trigger_alarm_wakeup(config_settings, manual_cap):
    if os.path.exists(DEEP_SLEEP_FILE):
        try: os.remove(DEEP_SLEEP_FILE)
        except: pass
    subprocess.Popen(["python3", "/home/pi/pipi_terminal/weather.py"])
    subprocess.Popen(["python3", "/home/pi/pipi_terminal/news_grabber.py"])
    selected_station = config_settings.get("selected_station_idx", 1)
    return selected_station, manual_cap

def get_light_effect_color(preset, ticks, alarm_elapsed=None):
    """
    Генератор каноничных световых пресетов SovIntel OS.
    alarm_elapsed: время в секундах с начала будильника. Если None — это тест (100% яркость).
    """
    # 1. Расчет коэффициента нарастания яркости за 30 секунд (от 5% до 100%)
    if alarm_elapsed is not None:
        dim_factor = 0.05 + (0.95 * min(1.0, alarm_elapsed / 30.0))
    else:
        dim_factor = 1.0  # Для теста в меню всегда полная мощность

    # 2. Вычисление базового цвета без учета димминга
    raw_color = (5, 10, 5)

    if preset == 0:
        # ПОЛИЦЕЙСКАЯ МИГАЛКА: ровно 1 секунда (1000 мс) на цвет
        raw_color = (255, 0, 0) if (ticks // 1000) % 2 == 0 else (0, 0, 255)

    elif preset == 1:
        # СТРОБОСКОП С МИКРОПАУЗАМИ: фазы по 200 мс (всего 16 фаз в цикле)
        # Б-выкл-Б-выкл-Б-черный-Ж-выкл-Ж-выкл-Ж-черный
        phase = (ticks // 200) % 16
        if phase in (0, 2, 4): raw_color = (255, 255, 255)      # 3 вспышки белого с паузами
        elif phase in (8, 10, 12): raw_color = (255, 255, 0)    # 3 вспышки желтого с паузами
        else: raw_color = (5, 10, 5)                             # Фазы тишины/выключения

    elif preset == 2:
        # ЗЕЛЕНОЕ ДЫХАНИЕ: плавный цикл 4 секунды (вверх-вниз)
        # От черно-зеленого (5,10,5) до мягкого светлого (20, 160, 40)
        sine = (math.sin((ticks / 4000.0) * (2 * math.pi)) + 1.0) / 2.0
        raw_color = (int(5 + 15 * sine), int(10 + 150 * sine), int(5 + 35 * sine))

    # 3. Применение плавного 30-секундного димминга
    return (int(raw_color[0] * dim_factor), int(raw_color[1] * dim_factor), int(raw_color[2] * dim_factor))
