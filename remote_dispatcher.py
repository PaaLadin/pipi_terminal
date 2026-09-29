# ====================================================================
# SovIntel TERMINAL REMOTE CONTROL DISPATCHER (MODULAR PART 1 OF 2)
# ====================================================================
import time
import os
import json
import vlc_engine

def handle_remote_event(ev_code, state):
    # МГНОВЕННЫЙ ПЕРЕХВАТ ЛЮБОЙ КНОПКИ ДЛЯ ВЫКЛЮЧЕНИЯ АКТИВНОГО БУДИЛЬНИКА
    if state.get("alarm_active"):
        state["alarm_active"] = False
        state["light_test_until"] = 0.0  # Сбрасываем мигание экрана
        vlc_engine.stop_audio()          # Намертво глушим радио/сирену
        print("БУДИЛЬНИК УСПЕШНО СБРОШЕН НАЖАТИЕМ КНОПКИ ПУЛЬТА!")
        return

    now = time.time()
    state["last_activity_time"] = now

    if "time_edit_mode" not in state:
        state["time_edit_mode"] = False

    # --- ЛОГИКА НОЧНОГО ПРОБУЖДЕНИЯ ЭКРАНА em713 ---
    if state["current_dim_factor"] == 0.05 and not state["is_daytime"]:
        if os.path.exists("/home/pi/pipi_terminal/.deep_sleep"):
            try: os.remove("/home/pi/pipi_terminal/.deep_sleep")
            except: pass
        if now - state.get("last_night_click_time", 0.0) <= 5.0:
            state["current_dim_factor"] = 0.75
        else:
            state["current_dim_factor"] = 0.50
            state["last_night_click_time"] = now
        return

    if not state["is_daytime"] and state["current_dim_factor"] > 0.05:
        state["current_dim_factor"] = 0.75

    # --- ГЛОБАЛЬНЫЕ МУЛЬТИМЕДИЙНЫЕ КНОПКИ ЗВУКА И КАНАЛОВ ---
    if ev_code == 115:
        state["manual_volume_cap"] = min(100, state["manual_volume_cap"] + 5)
        state["volume"] = state["manual_volume_cap"]
        state["is_muted"] = False
        vlc_engine.set_volume(state["volume"])
        state["show_vol_time"] = now
        return
    elif ev_code == 114:
        state["manual_volume_cap"] = max(0, state["manual_volume_cap"] - 5)
        state["volume"] = state["manual_volume_cap"]
        state["is_muted"] = False
        vlc_engine.set_volume(state["volume"])
        state["show_vol_time"] = now
        return
    elif ev_code == 113:
        state["is_muted"] = not state["is_muted"]
        vlc_engine.set_volume(0 if state["is_muted"] else state["volume"])
        state["show_vol_time"] = now
        return
    elif ev_code == 402:
        state["current_station_idx"] = (state["current_station_idx"] - 1) % len(vlc_engine.STATIONS)
        vlc_engine.play_station(state["current_station_idx"], state["volume"])
        return
    elif ev_code == 403:
        state["current_station_idx"] = (state["current_station_idx"] + 1) % len(vlc_engine.STATIONS)
        vlc_engine.play_station(state["current_station_idx"], state["volume"])
        return

    # --- СТРЕЛКА ВЛЕВО (105) ---
    if ev_code == 105:
        if state["time_edit_mode"]: return
        if state["active_tab"] == 5 and state["nav_focus"] == 'settings_sub':
            state["nav_focus"] = 'settings_main'
            if state["in_preview_mode"]:
                state["in_preview_mode"] = False
                vlc_engine.play_station(state["current_station_idx"], state["manual_volume_cap"])
        elif state["active_tab"] == 4 and state["nav_focus"] == 'content':
            state["weather_day_offset"] = max(0, state["weather_day_offset"] - 1)
        elif state["nav_focus"] == 'tabs' or state["active_tab"] != 5:
            state["active_tab"] = (state["active_tab"] - 1) % len(state["MODULES"])
            state["nav_focus"] = 'tabs'
            state["news_cursor"] = 0
        return

    # --- СТРЕЛКА ВПРАВО (106) ---
    elif ev_code == 106:
        if state["time_edit_mode"]: return
        if state["active_tab"] == 5 and state["nav_focus"] == 'settings_main':
            state["nav_focus"] = 'settings_sub'
            state["sub_cursor"] = 0
        elif state["active_tab"] == 4 and state["nav_focus"] == 'content':
            state["weather_day_offset"] = min(2, state["weather_day_offset"] + 1)
        elif state["nav_focus"] == 'tabs' or state["active_tab"] != 5:
            state["active_tab"] = (state["active_tab"] + 1) % len(state["MODULES"])
            state["nav_focus"] = 'tabs'
            state["news_cursor"] = 0
        return

    # --- СТРЕЛКА ВВЕРХ (103) ---
    elif ev_code == 103:
        # Режим «магнита»: если активен захват времени, накручиваем параметры вверх
        if state["active_tab"] == 5 and state["nav_focus"] == "settings_sub" and state["content_cursor"] == 0 and state["time_edit_mode"]:
            try:
                h, m = map(int, state["config_settings"].get("alarm_time", "07:00").split(":"))
                if state["sub_cursor"] == 0: h = (h + 1) % 24
                else: m = (m + 5) % 60
                state["config_settings"]["alarm_time"] = f"{h:02d}:{m:02d}"
                with open("/home/pi/pipi_terminal/config.json", "w") as f: json.dump(state["config_settings"], f, indent=2)
            except: pass
            return

        if state["active_tab"] == 5:
            if state["nav_focus"] == 'settings_main' and state["content_cursor"] > 0:
                state["content_cursor"] -= 1
            elif state["nav_focus"] == 'settings_main' and state["content_cursor"] == 0:
                state["nav_focus"] = 'tabs'
            elif state["nav_focus"] == 'settings_sub' and state["sub_cursor"] > 0:
                state["sub_cursor"] -= 1
        else:
            if state["nav_focus"] == 'content' and state["active_tab"] not in (3, 4):
                state["nav_focus"] = 'tabs'
            elif state["active_tab"] == 3:
                if state["news_cursor"] > 0: state["news_cursor"] -= 1
                else: state["nav_focus"] = 'tabs'
            elif state["active_tab"] == 4:
                if state["weather_graph_idx"] > 0: state["weather_graph_idx"] -= 1
                else: state["nav_focus"] = 'tabs'
        return

    # --- СТРЕЛКА ВНИЗ (108) ---
    elif ev_code == 108:
        # Режим «магнита»: если активен захват времени, уменьшаем параметры вниз
        if state["active_tab"] == 5 and state["nav_focus"] == "settings_sub" and state["content_cursor"] == 0 and state["time_edit_mode"]:
            try:
                h, m = map(int, state["config_settings"].get("alarm_time", "07:00").split(":"))
                if state["sub_cursor"] == 0: h = (h - 1) % 24
                else: m = (m - 5) % 60
                state["config_settings"]["alarm_time"] = f"{h:02d}:{m:02d}"
                with open("/home/pi/pipi_terminal/config.json", "w") as f: json.dump(state["config_settings"], f, indent=2)
            except: pass
            return

        if state["nav_focus"] == 'tabs':
            state["nav_focus"] = 'settings_main' if state["active_tab"] == 5 else 'content'
            if state["active_tab"] == 5: state["content_cursor"] = 0
        elif state["active_tab"] == 5:
            if state["nav_focus"] == 'settings_main' and state["content_cursor"] < 4:
                state["content_cursor"] += 1
            elif state["nav_focus"] == 'settings_sub':
                max_sub = 1 if state["content_cursor"] == 0 else (len(vlc_engine.STATIONS) if state["content_cursor"] == 1 else 2 if state["content_cursor"] == 2 else 3)
                state["sub_cursor"] = (state["sub_cursor"] + 1) % (max_sub + 1)
        else:
            if state["active_tab"] == 4 and state["weather_graph_idx"] < 4:
                state["weather_graph_idx"] += 1
            elif state["active_tab"] == 3:
                try:
                    with open('/home/pi/pipi_terminal/news.txt', 'r', encoding='utf-8') as nf:
                        total_news = len([l for l in nf if l.strip()])
                    if state["news_cursor"] < min(20, total_news - 1): state["news_cursor"] += 1
                except:
                    if state["news_cursor"] < 20: state["news_cursor"] += 1
        return

    # --- КНОПКА ОК / ENTER (353) ---
    elif ev_code == 353:
        if state["active_tab"] == 5:
            if state["nav_focus"] in ("settings_main", "content"):
                if state["content_cursor"] == 0:
                    state["config_settings"]["alarm_enabled"] = not state["config_settings"].get("alarm_enabled", True)
                elif state["content_cursor"] == 1:
                    state["config_settings"]["alarm_audio_enabled"] = not state["config_settings"].get("alarm_audio_enabled", True)
                elif state["content_cursor"] == 2:
                    state["config_settings"]["light_signal_enabled"] = not state["config_settings"].get("light_signal_enabled", True)
                
                with open("/home/pi/pipi_terminal/config.json", "w") as f:
                    json.dump(state["config_settings"], f, indent=2)

            elif state["nav_focus"] == "settings_sub":
                if state["content_cursor"] == 0:
                    # Инвертируем состояние «магнита» времени без прибавления значений
                    state["time_edit_mode"] = not state["time_edit_mode"]
                elif state["content_cursor"] == 1:
                    if state["sub_cursor"] == 0:
                        state["config_settings"]["use_custom_alarm_sound"] = True
                    else:
                        state["config_settings"]["use_custom_alarm_sound"] = False
                        state["config_settings"]["selected_station_idx"] = state["sub_cursor"] - 1
                        vlc_engine.play_station(state["sub_cursor"] - 1, state["manual_volume_cap"])
                        state["preview_start_time"] = time.time()
                        state["in_preview_mode"] = True
                elif state["content_cursor"] == 2:
                    # Если пресет уже выбран - запускаем 3-секундный визуальный тест
                    if state["config_settings"].get("selected_light_preset") == state["sub_cursor"]:
                        state["light_test_until"] = time.time() + 3.0
                    else:
                        state["config_settings"]["selected_light_preset"] = state["sub_cursor"]
                elif state["content_cursor"] == 3:
                    state["current_theme"] = state["sub_cursor"]
                    state["config_settings"]["default_theme_idx"] = state["current_theme"]
                elif state["content_cursor"] == 4:
                    if state["sub_cursor"] in (0, 1): state["running"] = False; state["reboot_requested"] = True
                    elif state["sub_cursor"] == 2: os.system("sudo reboot")
                    elif state["sub_cursor"] == 3: os.system("sudo poweroff")
                
                with open("/home/pi/pipi_terminal/config.json", "w") as f:
                    json.dump(state["config_settings"], f, indent=2)
        return
