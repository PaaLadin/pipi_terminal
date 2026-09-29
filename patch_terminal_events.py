            # Дополнительные переменные для OSD-превью аудиоисточников
            if 'sub_cursor' not in globals(): sub_cursor = 0
            if 'preview_start_time' not in globals(): preview_start_time = 0.0
            if 'in_preview_mode' not in globals(): in_preview_mode = False

            # Остановка 10-секундного превью радиостанции по таймауту
            if in_preview_mode and time.time() - preview_start_time >= 10.0:
                in_preview_mode = False
                vlc_engine.play_station(current_station_idx, manual_volume_cap)

            # --- ВЛЕВО (KEY_LEFT) ---
            if ev_code == 105:
                if nav_focus == 'tabs': active_tab = (active_tab - 1) % len(MODULES)
                elif active_tab == 5 and nav_focus == 'settings_sub':
                    nav_focus = 'settings_main'  # Возврат из правой OSD-панели в левую
                    if in_preview_mode: 
                        in_preview_mode = False
                        vlc_engine.play_station(current_station_idx, manual_volume_cap)
                elif active_tab == 3 and nav_focus == 'content': active_tab = (active_tab - 1) % len(MODULES); news_cursor = 0
                elif active_tab == 4 and nav_focus == 'content': weather_day_offset = (weather_day_offset - 1) % 3
                elif active_tab == 1 and nav_focus == 'content':
                    current_station_idx = (current_station_idx - 1) % len(STATIONS)
                    vlc_engine.play_station(current_station_idx, volume)

            # --- ВПРАВО (KEY_RIGHT) ---
            elif ev_code == 106:
                if nav_focus == 'tabs': active_tab = (active_tab + 1) % len(MODULES)
                elif active_tab == 5 and nav_focus == 'settings_main':
                    nav_focus = 'settings_sub'  # Вход в правое подменю OSD
                    sub_cursor = 0
                elif active_tab == 3 and nav_focus == 'content': active_tab = (active_tab + 1) % len(MODULES); news_cursor = 0
                elif active_tab == 4 and nav_focus == 'content': weather_day_offset = (weather_day_offset + 1) % 3
                elif active_tab == 1 and nav_focus == 'content':
                    current_station_idx = (current_station_idx + 1) % len(STATIONS)
                    vlc_engine.play_station(current_station_idx, volume)

            # --- ВВЕРХ (KEY_UP) ---
            elif ev_code == 103:
                if nav_focus == 'settings_main' and content_cursor > 0: content_cursor -= 1
                elif nav_focus == 'settings_main' and content_cursor == 0: nav_focus = 'tabs'
                elif nav_focus == 'settings_sub' and sub_cursor > 0: sub_cursor -= 1
                elif nav_focus == 'content' and active_tab not in (3, 4, 5): nav_focus = 'tabs'
                elif active_tab == 5 and content_cursor > 0 and nav_focus == 'content': content_cursor -= 1
                elif active_tab == 3:
                    if news_cursor > 0: news_cursor -= 1
                    else: nav_focus = 'tabs'
                elif active_tab == 4:
                    if nav_focus == 'content' and weather_graph_idx > 0: weather_graph_idx -= 1
                    elif nav_focus == 'content' and weather_graph_idx == 0: nav_focus = 'tabs'

            # --- ВНИЗ (KEY_DOWN) ---
            elif ev_code == 108:
                if nav_focus == 'tabs': 
                    nav_focus = 'settings_main' if active_tab == 5 else 'content'
                elif nav_focus == 'settings_main' and content_cursor < 4: content_cursor += 1
                elif nav_focus == 'settings_sub':
                    # Считаем лимиты строк правых панелей
                    max_sub = 1 if content_cursor == 0 else (len(STATIONS) if content_cursor == 1 else 1 if content_cursor == 2 else 3)
                    if sub_cursor < max_sub: sub_cursor += 1
                elif active_tab == 5 and content_cursor < 5 and nav_focus == 'content': content_cursor += 1
                elif active_tab == 4 and nav_focus == 'content' and weather_graph_idx < 4: weather_graph_idx += 1
                elif active_tab == 3 and nav_focus == 'content':
                    try:
                        with open('/home/pi/pipi_terminal/news.txt', 'r', encoding='utf-8') as nf: total_news = len([l for l in nf if l.strip()])
                        if news_cursor < min(20, total_news - 1): news_cursor += 1
                    except:
                        if news_cursor < 20: news_cursor += 1

            # --- НАЖАТИЕ КНОПКИ OK / ENTER (ОБРАБОТКА ЧЕКБОКСОВ) ---
            elif ev_code == 28:
                import json
                # Логика левой панели: мгновенный переключатель [on/off]
                if nav_focus == "settings_main":
                    if content_cursor == 0:
                        config_settings["alarm_enabled"] = not config_settings.get("alarm_enabled", True)
                    elif content_cursor == 1:
                        config_settings["alarm_audio_enabled"] = not config_settings.get("alarm_audio_enabled", True)
                    elif content_cursor == 2:
                        config_settings["light_signal_enabled"] = not config_settings.get("light_signal_enabled", True)
                    
                    # Запись конфига в config.json на лету
                    with open("/home/pi/pipi_terminal/config.json", "w") as f:
                        json.dump(config_settings, f, indent=2)

                # Логика правой панели: детальная калибровка
                elif nav_focus == "settings_sub":
                    if content_cursor == 0: # Смена времени будильника
                        h, m = map(int, config_settings.get("alarm_time", "07:00").split(":"))
                        if sub_cursor == 0: h = (h + 1) % 24
                        else: m = (m + 5) % 60
                        config_settings["alarm_time"] = f"{h:02d}:{m:02d}"
                    
                    elif content_cursor == 1: # Выбор аудиоисточника + 10 сек превью
                        if sub_cursor == 0:
                            config_settings["use_custom_alarm_sound"] = True
                            # Имитация короткого писка
                        else:
                            config_settings["use_custom_alarm_sound"] = False
                            config_settings["selected_station_idx"] = sub_cursor - 1
                            vlc_engine.play_station(sub_cursor - 1, manual_volume_cap)
                            preview_start_time = time.time()
                            in_preview_mode = True

                    elif content_cursor == 2: # Пресеты вспышек
                        config_settings["selected_light_preset"] = sub_cursor

                    elif content_cursor == 3: # Смена темы PiPi-Boy
                        current_theme = sub_cursor
                        config_settings["default_theme_idx"] = current_theme

                    elif content_cursor == 4: # Менеджер питания системы
                        if sub_cursor == 0: pass # Принудительный ребут аппки
                        elif sub_cursor == 1: running = False
                        elif sub_cursor == 2: os.system("sudo reboot")
                        elif sub_cursor == 3: os.system("sudo poweroff")

                    with open("/home/pi/pipi_terminal/config.json", "w") as f:
                        json.dump(config_settings, f, indent=2)
