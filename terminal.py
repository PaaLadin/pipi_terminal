# ====================================================================
# SovIntel TERMINAL MAIN DISPATCHER CORE UNIT (MODULAR AUDIO FIXED v6.1)
# ====================================================================
# Исправленная версия ядра. Управляет аудиосистемой без перегрузки сети.
# Хранит глобальное состояние в единой структуре для синхронизации с пультом.

import pygame
import sys
import os
import time
from datetime import datetime

import vlc_engine
import sleep_daemon
import remote
import remote_dispatcher # Импортируем наш новый изолированный модуль пульта

def apply_dimming(color, factor):
    r, g, b = color
    return (int(r * factor), int(g * factor), int(b * factor))

pygame.init()
# # remote_listener = remote.RemoteListener()

# Параметры видеорежима экрана em713
WIDTH, HEIGHT = 1024, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)
pygame.display.set_caption("SovIntel OS Terminal v6.1")

# Глобальные каноничные палитры PiPi-Boy
THEME_COLORS = [
    (0, 255, 65),    # Classic PiPi-Boy Green
    (255, 182, 66),  # Amber Radiation
    (30, 144, 255),  # SovIntel Blue
    (255, 255, 255)  # White Phosphor
]
BG_COLOR = (5, 10, 5)

# Единый глобальный словарь состояния для передачи в диспетчер пульта
state = {
    "MODULES": ["MATRIX", "DASHBOARD", "CLOCK", "NEWS", "WEATHER", "SETTINGS"],
    "active_tab": 1,
    "nav_focus": "content",
    "current_theme": 0,
    
    # Звуковой тракт (Управление лимитами и громкостью)
    "volume": 10,
    "manual_volume_cap": 10,
    "is_muted": False,
    "show_vol_time": 0.0,
    "current_station_idx": 1,
    "in_preview_mode": False,
    "preview_start_time": 0.0,
    
    # Состояние дисплея и таймеры
    "last_activity_time": time.time(),
    "current_dim_factor": 1.0,
    "last_night_click_time": 0.0,
    "is_daytime": True,
    "running": True,
    
    # Курсоры OSD-меню
    "content_cursor": 0,
    "sub_cursor": 0,
    "news_cursor": 0,
    "weather_graph_idx": 0,
    "weather_day_offset": 0,
    
    # Настройки конфигурации
    "config_settings": {}
}

weather_data = []
news_scroll_x = 1024

def load_external_data():
    global weather_data
    if os.path.exists("/home/pi/pipi_terminal/weather.txt"):
        try:
            with open("/home/pi/pipi_terminal/weather.txt", "r", encoding="utf-8") as wf:
                weather_data = wf.readlines()
        except: pass
    if os.path.exists("/home/pi/pipi_terminal/config.json"):
        import json
        try:
            with open("/home/pi/pipi_terminal/config.json", "r") as cjf:
                state["config_settings"] = json.load(cjf)
                state["current_theme"] = state["config_settings"].get("default_theme_idx", 0)
        except: pass

# Первичный запуск систем данных
load_external_data()
import remote
remote_listener = remote.RemoteListener()
from screens import matrix_screen, dash_screen, clock_screen, news_screen, weather_screen, settings_screen

fonts = {
    "sm": pygame.font.SysFont("Courier", 18, bold=True),
    "md": pygame.font.SysFont("Courier", 24, bold=True),
    "bg": pygame.font.SysFont("Courier", 54, bold=True),
    "huge": pygame.font.SysFont("Courier", 110, bold=True)
}
clock = pygame.time.Clock()

# Фикс: Инициализируем громкость в VLC строго один раз при старте, без спама в цикле!
vlc_engine.set_volume(state["manual_volume_cap"])
vlc_engine.play_station(state["current_station_idx"], state["manual_volume_cap"])

if os.path.exists("/home/pi/pipi_terminal/.deep_sleep"):
    os.remove("/home/pi/pipi_terminal/.deep_sleep")

# Сохраняем предыдущий уровень громкости для отслеживания реальных изменений демона
last_applied_volume = state["volume"]
last_alarm_check_minute = -1

while state["running"]:
    dt_now = datetime.now()
    state["is_daytime"] = (7 <= dt_now.hour < 23)
    now = time.time()
    inactivity_sec = now - state["last_activity_time"]

    # Сброс 10-секундного аудиопревью радиостанции по таймауту
    if state["in_preview_mode"] and now - state["preview_start_time"] >= 10.0:
        state["in_preview_mode"] = False
        vlc_engine.play_station(state["current_station_idx"], state["manual_volume_cap"])
        last_applied_volume = state["manual_volume_cap"]

    # Обновление состояния энергосбережения через sleep_daemon
    updated_tab, _, current_dim_factor, target_vol, _ = sleep_daemon.update_energy_state(
        now, inactivity_sec, state["active_tab"], 
        state["nav_focus"] if state["active_tab"] == 5 else "content", 
        state["manual_volume_cap"], state["volume"], state["is_muted"]
    )
    
    state["active_tab"] = updated_tab
    state["current_dim_factor"] = current_dim_factor

    # Коррекция звукового тракта на заставках и рабочих экранах
    if not state["is_muted"] and not state["in_preview_mode"]:
        if state["active_tab"] in (0, 2):
            state["volume"] = target_vol
        else:
            state["volume"] = state["manual_volume_cap"]
        
        # ФИКС: Отправляем громкость в VLC только если она реально изменилась под управлением демона!
        if state["volume"] != last_applied_volume:
            vlc_engine.set_volume(state["volume"])
            last_applied_volume = state["volume"]
    # Логика работы будильника (срабатывает один раз в минуту)
    if state["config_settings"].get("alarm_enabled", False) and dt_now.minute != last_alarm_check_minute:
        last_alarm_check_minute = dt_now.minute
        al_h, al_m = map(int, state["config_settings"].get("alarm_time", "07:00").split(":"))
        if dt_now.hour == al_h and dt_now.minute == al_m:
            state["last_activity_time"] = now
            state["current_dim_factor"] = 1.0
            state["is_muted"] = False
            sel_station, alarm_vol = sleep_daemon.trigger_alarm_wakeup(state["config_settings"], state["manual_volume_cap"])
            state["current_station_idx"] = sel_station
            
            # ВЗВОДИМ АКТИВНЫЙ БУДИЛЬНИК И ТАЙМЕРЫ РАССВЕТА
            state["alarm_active"] = True
            state["alarm_start_time"] = time.time()
            state["alarm_expires_at"] = time.time() + 600.0
            # Запускаем целевую станцию со стартовой громкостью 10% вместо нуля
            state["volume"] = max(10, int(alarm_vol * 0.05))
            vlc_engine.play_station(state["current_station_idx"], state["volume"])
            last_applied_volume = state["volume"]
            # ВЗВОДИМ АКТИВНЫЙ БУДИЛЬНИК НА 10 МИНУТ (600 СЕКУНД)
            state["alarm_active"] = True
            state["alarm_expires_at"] = time.time() + 600.0
            load_external_data()

    # Считывание и фильтрация входящих событий пульта
    # Опрос физического Bluetooth пульта напрямую из буфера evdev
    remote_code = remote_listener.poll_keys()
    if remote_code is not None:
        remote_dispatcher.handle_remote_event(remote_code, state)
        last_applied_volume = state["volume"]

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state["running"] = False
        elif event.type == pygame.USEREVENT:
            ev_code = getattr(event, 'code', None)
            if ev_code is None: continue

            # Передаем обработку кнопкам в изолированный диспетчер пульта
            remote_dispatcher.handle_remote_event(ev_code, state)
            # Синхронизируем маркер громкости после ручных изменений с пульта
            last_applied_volume = state["volume"]

    # ====================================================================
    # ГРАФИЧЕСКИЙ РЕНДЕРИНГ КАДРА И ОТРИСОВКА ЭКРАНОВ С УЧЕТОМ ДИММИНГА
    # ====================================================================
    # --- БЛОК ДИНАМИЧЕСКИХ СВЕТОВЫХ ЭФФЕКТОВ БУДИЛЬНИКА И ТЕСТА ---
    # Проверяем автоматический сброс будильника по таймауту 10 минут
    if state.get("alarm_active"):
        global last_volume_fade_time
        if time.time() > state.get("alarm_expires_at", 0.0):
            state["alarm_active"] = False
            vlc_engine.stop_audio()
        else:
            current_sec_tick = int(time.time())
            if "last_volume_fade_time" not in globals() or current_sec_tick != globals().get("last_volume_fade_time", 0):
                globals()["last_volume_fade_time"] = current_sec_tick
                elapsed = time.time() - state.get("alarm_start_time", time.time())
                
                if int(elapsed) == 1:
                    fake_station = (state["current_station_idx"] + 1) % len(vlc_engine.STATIONS)
                    vlc_engine.play_station(fake_station, 15)
                    pygame.time.wait(250)
                    vlc_engine.play_station(state["current_station_idx"], 15)

                # Защита от нуля: если manual_volume_cap скручен, базовая громкость будильника = 70
                base_cap = state["manual_volume_cap"] if state["manual_volume_cap"] > 0 else 70
                sound_factor = 0.20 + (0.80 * min(1.0, elapsed / 30.0))
                target_alarm_vol = int(base_cap * sound_factor)
                
                if state.get("volume") != target_alarm_vol:
                    state["volume"] = target_alarm_vol
                    vlc_engine.set_volume(target_alarm_vol)
                    
    is_testing_light = time.time() < state.get("light_test_until", 0.0)
    is_alarm_light = state.get("alarm_active") and state["config_settings"].get("light_signal_enabled", False)

    if is_testing_light or is_alarm_light:
        preset = state["config_settings"].get("selected_light_preset", 0)
        elapsed_sec = (time.time() - state.get("alarm_start_time", time.time())) if is_alarm_light else None
        BASE_COLOR = sleep_daemon.get_light_effect_color(preset, pygame.time.get_ticks(), elapsed_sec)
    else:
        BASE_COLOR = apply_dimming(THEME_COLORS[state["current_theme"]], state["current_dim_factor"])
    TEXT_DIM_COLOR = apply_dimming(BASE_COLOR, 0.4)
    GRID_COLOR = apply_dimming(BASE_COLOR, 0.15)

    # Проверяем, активен ли полноэкранный световой эффект (тест или живой будильник)
    is_light_active = time.time() < state.get("light_test_until", 0.0) or (state.get("alarm_active") and state["config_settings"].get("light_signal_enabled", False))
    
    if is_light_active:
        preset = state["config_settings"].get("selected_light_preset", 0)
        # Получаем динамический цвет эффекта из слип-демона
        EFFECT_COLOR = sleep_daemon.get_light_effect_color(preset, pygame.time.get_ticks())
        screen.fill(EFFECT_COLOR)
        
        # Отрисовываем только короткую подсказку внизу, чтобы пользователь знал, как выключить
        help_txt = fonts["sm"].render("PRESS ANY KEY ON REMOTE TO DISMISS ALARM", True, (0,0,0) if sum(EFFECT_COLOR) > 400 else (255,255,255))
        screen.blit(help_txt, (20, HEIGHT - 25))
        
        pygame.display.flip()
        clock.tick(30)
        continue

    screen.fill(BG_COLOR)

    # Фоновая сетка SovIntel (Отключаем на экране MATRIX)
    if state["active_tab"] != 0:
        for x in range(0, WIDTH, 40): pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 40): pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y))

    # Верхняя панель вкладок PiPi-Boy (Отключаем на экране MATRIX)
    if state["active_tab"] != 0:
        tab_x = 20
        for i, mod_title in enumerate(state["MODULES"]):
            if i == state["active_tab"]:
                lbl_text = f"[{mod_title}]" if state["nav_focus"] in ('tabs', 'settings_main') else f" {mod_title} "
                txt = fonts["md"].render(lbl_text, True, BASE_COLOR)
            else:
                txt = fonts["md"].render(f" {mod_title} ", True, TEXT_DIM_COLOR)
            screen.blit(txt, (tab_x, 15))
            tab_x += txt.get_width() + 25
        pygame.draw.line(screen, BASE_COLOR, (10, 45), (WIDTH - 10, 45), 2)

    # Вызовы модулей отрисовки контента вкладок
    if state["active_tab"] == 0: 
        matrix_screen.draw(screen, WIDTH, HEIGHT, BASE_COLOR)
    elif state["active_tab"] == 1: 
        dash_screen.draw(screen, fonts, vlc_engine.STATIONS, state["current_station_idx"], False, weather_data, BASE_COLOR, news_scroll_x)
    elif state["active_tab"] == 2: 
        clock_screen.draw(screen, fonts, state["config_settings"], BASE_COLOR)
    elif state["active_tab"] == 3: 
        news_screen.draw(screen, fonts, state["config_settings"], TEXT_DIM_COLOR, BASE_COLOR, state["nav_focus"], state["news_cursor"])
    elif state["active_tab"] == 4: 
        weather_screen.draw(screen, fonts, weather_data, BASE_COLOR, BASE_COLOR, state["nav_focus"], state["weather_graph_idx"], state["weather_day_offset"])
    elif state["active_tab"] == 5: 
        settings_screen.draw(screen, fonts, state["config_settings"], state["content_cursor"], BASE_COLOR, state["nav_focus"], state["sub_cursor"], state["current_theme"], vlc_engine.STATIONS)

    # OSD индикатор изменения громкости (VOL)
    if now - state["show_vol_time"] < 2.5:
        vol_box = pygame.Surface((220, 45)); vol_box.fill((10, 20, 10))
        pygame.draw.rect(vol_box, BASE_COLOR, (0, 0, 220, 45), 2)
        v_disp = 0 if state["is_muted"] else state["manual_volume_cap"]
        v_txt = fonts["md"].render(f"VOL: {v_disp}%", True, BASE_COLOR)
        vol_box.blit(v_txt, (10, 10))
        num_bars = v_disp // 10
        for b in range(10):
            bar_color = BASE_COLOR if b < num_bars else GRID_COLOR
            pygame.draw.rect(vol_box, bar_color, (120 + b * 9, 15, 6, 18))
        screen.blit(vol_box, (WIDTH - 240, HEIGHT - 65))

    # Нижняя строчка подсказок горячих клавиш пульта
    if state["active_tab"] != 0:
        help_str = "NAV: [< >] TAB  [^ v] SELECT  [OK] ENTER" if state["nav_focus"] == 'tabs' else "NAV: [^] BACK TO TABS  [v] MOVE"
        help_txt = fonts["sm"].render(help_str, True, TEXT_DIM_COLOR)
        screen.blit(help_txt, (20, HEIGHT - 25))

    # Сдвиг бегущей строки новостей
    news_scroll_x -= 3
    try:
        with open("/home/pi/pipi_terminal/.marquee_width", "r") as f: max_limit = -int(f.read().strip())
    except: max_limit = -4000
    if news_scroll_x < max_limit: news_scroll_x = WIDTH

    pygame.display.flip()
    clock.tick(30)

# ====================================================================
# ДЕИНИЦИАЛИЗАЦИЯ И КОРРЕКТНОЕ ЗАКРЫТИЕ ПОТОКОВ
# ====================================================================
vlc_engine.stop_audio()
if os.path.exists("/home/pi/pipi_terminal/.deep_sleep"):
    try: os.remove("/home/pi/pipi_terminal/.deep_sleep")
    except: pass
pygame.quit()
if state.get("reboot_requested"):
    sys.exit(5)  # Специальный код возврата для systemd для мгновенного рестарта
else:
    sys.exit(0)
sys.exit()
