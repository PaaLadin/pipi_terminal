# ====================================================================
# SovIntel OS TWO-LEVEL OSD CONFIGURATION MATRIX INTERFACE
# ====================================================================
import pygame

def draw_osd_frame(surface, color, rect, thickness=2):
    """Отрисовка разделительных линий OSD меню в стиле PiPi-Boy"""
    x, y, w, h = rect
    pygame.draw.rect(surface, color, rect, thickness)

def draw(screen, fonts, config_settings, content_cursor, text_color, 
         nav_focus="content", sub_cursor=0, current_theme=0, stations=[], alarm_sound_playing=False):
    """
    Двухуровневый интерактивный OSD-интерфейс настроек SovIntel OS.
    Разделяет экран на левую (главную) и правую (дочернюю) панели.
    """
    font_md = fonts["md"]
    font_sm = fonts["sm"]
    
    # 1. Общий заголовок экрана настроек
    header_surf = font_md.render("--- TERMINAL OSD SYSTEM CONFIGURATION ---", True, text_color)
    screen.blit(header_surf, (50, 65))
    
    # Считываем текущие параметры из памяти/конфига
    alarm_time = config_settings.get("alarm_time", "07:00")
    is_alarm_enabled = config_settings.get("alarm_enabled", True)
    is_alarm_audio_enabled = config_settings.get("alarm_audio_enabled", True)
    selected_station = config_settings.get("selected_station_idx", 1)
    use_custom_sound = config_settings.get("use_custom_alarm_sound", False)
    light_signal_enabled = config_settings.get("light_signal_enabled", False)
    selected_light_preset = config_settings.get("selected_light_preset", 0)
    
    # Сетка тем и подменю питания
    theme_names = ["CLASSIC GREEN", "AMBER RADIATION", "SovIntel BLUE", "WHITE PHOSPHOR"]
    power_options = ["REBOOT APPLICATION", "EXIT TO TERMINAL CLI", "REBOOT SYSTEM (OS)", "SHUTDOWN SYSTEM (OS)"]
    light_presets = ["RED / BLUE FLASH", "WHITE / YELLOW STROBE", "SOFT GREEN GRADIENT"]

    # 2. Формирование главного левого меню (5 основных пунктов)
    # Нажатие OK на этих строках переключает базовый чекбокс [on/off]
    main_items = [
        f"1. ALARM CLOCK TIMER [{'ON ' if is_alarm_enabled else 'OFF'}]",
        f"2. ALARM AUDIO STREAM [{'ON ' if is_alarm_enabled and is_alarm_audio_enabled else 'OFF'}]",
        f"3. VISUAL LIGHT WARNING [{'ON ' if light_signal_enabled else 'OFF'}]",
        f"4. DEFAULT SovIntel THEME",
        f"5. SYSTEM POWER LEVEL"
    ]
    
    split_x = 440  # Координата разделения левой и правой панели OSD
    
    # Отрисовка левой панели главных настроек
    for idx, item in enumerate(main_items):
        y_pos = 130 + (idx * 55)
        
        # Определяем подсветку активной строки главного меню
        if nav_focus == "settings_main" and content_cursor == idx:
            line_color = text_color
            screen.blit(font_sm.render("> ", True, text_color), (35, y_pos + 2))
        elif nav_focus == "settings_sub" and content_cursor == idx:
            # Если мы ушли в правое подменю, левый пункт горит тускло, но сохраняет рамку выборки
            line_color = (int(text_color[0]*0.5), int(text_color[1]*0.5), int(text_color[2]*0.5))
            screen.blit(font_sm.render("* ", True, line_color), (35, y_pos + 2))
        else:
            line_color = (int(text_color[0]*0.4), int(text_color[1]*0.4), int(text_color[2]*0.4))
            
        surf = font_sm.render(item, True, line_color)
        screen.blit(surf, (60, y_pos))
        
        # Декоративная тонкая рамка вокруг каждого главного OSD-пункта
        if content_cursor == idx and nav_focus in ("settings_main", "settings_sub"):
            pygame.draw.rect(screen, text_color, (50, y_pos - 8, split_x - 70, 42), 1)

    # Вертикальная разделительная линия OSD между панелями
    pygame.draw.line(screen, (int(text_color[0]*0.3), int(text_color[1]*0.3), int(text_color[2]*0.3)), (split_x, 115), (split_x, 480), 2)

    # ====================================================================
    # БЛОК 2: РЕНДЕРИНГ ПРАВОЙ ПАНЕЛИ (ПОДМЕНЮ КОНТЕНТА)
    # ====================================================================
    sub_x = split_x + 30  # Начальная координата X для правого контента
    sub_y_start = 130     # Начальная координата Y для пунктов подменю
    
    # Заголовок правой панели
    sub_header_surf = font_sm.render("--- CONTROL OPTIONS ---", True, (int(text_color[0]*0.5), int(text_color[1]*0.5), int(text_color[2]*0.5)))
    screen.blit(sub_header_surf, (sub_x, 95))

    # ----------------------------------------------------
    # ПОДМЕНЮ 1.1: НАСТРОЙКА ВРЕМЕНИ БУДИЛЬНИКА
    # ----------------------------------------------------
    if content_cursor == 0:
        h_str, m_str = alarm_time.split(":")
        sub_items = [
            f"HOUR:   < {h_str} >",
            f"MINUTE: < {m_str} >"
        ]
        for idx, item in enumerate(sub_items):
            y = sub_y_start + (idx * 45)
            is_active = (nav_focus == "settings_sub" and sub_cursor == idx)
            color = text_color if is_active else (int(text_color[0]*0.4), int(text_color[1]*0.4), int(text_color[2]*0.4))
            
            if is_active:
                screen.blit(font_sm.render("> ", True, text_color), (sub_x - 20, y))
            screen.blit(font_sm.render(item, True, color), (sub_x, y))

    # ----------------------------------------------------
    # ПОДМЕНЮ 2.1: ВЫБОР АУДИОПОТОКА (РАДИОСТАНЦИИ ИЛИ СИГНАЛ)
    # ----------------------------------------------------
    elif content_cursor == 1:
        # Формируем динамический список аудиоисточников
        audio_list = []
        audio_list.append(f"[ {'x' if use_custom_sound else ' '} ] COMPACT ALARM.SOUND")
        
        # Добавляем радиостанции из переданного списка vlc_engine
        for s_idx, st in enumerate(stations):
            is_chk = (not use_custom_sound and selected_station == s_idx)
            audio_list.append(f"[ {'x' if is_chk else ' '} ] {st['name'][:24].upper()}")
            
        # Выводим список на экран с возможностью вертикального скролла
        for idx, item in enumerate(audio_list):
            y = sub_y_start + (idx * 40)
            if y > 460: break  # Ограничение по высоте правой OSD-панели
            
            is_active = (nav_focus == "settings_sub" and sub_cursor == idx)
            color = text_color if is_active else (int(text_color[0]*0.4), int(text_color[1]*0.4), int(text_color[2]*0.4))
            
            if is_active:
                screen.blit(font_sm.render("> ", True, text_color), (sub_x - 20, y))
            screen.blit(font_sm.render(item, True, color), (sub_x, y))

    # ----------------------------------------------------
    # ПОДМЕНЮ 3.1: ЦВЕТОВАЯ СВЕТОВАЯ СИГНАЛИЗАЦИЯ
    # ----------------------------------------------------
    elif content_cursor == 2:
        for idx, preset in enumerate(light_presets):
            y = sub_y_start + (idx * 45)
            is_chk = (selected_light_preset == idx)
            display_str = f"[ {'x' if is_chk else ' '} ] {preset}"
            
            is_active = (nav_focus == "settings_sub" and sub_cursor == idx)
            color = text_color if is_active else (int(text_color[0]*0.4), int(text_color[1]*0.4), int(text_color[2]*0.4))
            
            if is_active:
                screen.blit(font_sm.render("> ", True, text_color), (sub_x - 20, y))
            screen.blit(font_sm.render(display_str, True, color), (sub_x, y))

    # ----------------------------------------------------
    # ПОДМЕНЮ 4.1: ВЫБОР ДЕФОЛТНОЙ СИТЕМНОЙ ТЕМЫ ОФОРМЛЕНИЯ
    # ----------------------------------------------------
    elif content_cursor == 3:
        for idx, theme in enumerate(theme_names):
            y = sub_y_start + (idx * 45)
            is_chk = (current_theme == idx)
            display_str = f"[ {'x' if is_chk else ' '} ] {theme}"
            
            is_active = (nav_focus == "settings_sub" and sub_cursor == idx)
            color = text_color if is_active else (int(text_color[0]*0.4), int(text_color[1]*0.4), int(text_color[2]*0.4))
            
            if is_active:
                screen.blit(font_sm.render("> ", True, text_color), (sub_x - 20, y))
            screen.blit(font_sm.render(display_str, True, color), (sub_x, y))

    # ----------------------------------------------------
    # ПОДМЕНЮ 5.1: МЕНЕДЖЕР ПИТАНИЯ ХОСТА (POWER MANAGEMENT)
    # ----------------------------------------------------
    elif content_cursor == 4:
        for idx, opt in enumerate(power_options):
            y = sub_y_start + (idx * 45)
            
            is_active = (nav_focus == "settings_sub" and sub_cursor == idx)
            color = text_color if is_active else (int(text_color[0]*0.4), int(text_color[1]*0.4), int(text_color[2]*0.4))
            
            if is_active:
                screen.blit(font_sm.render("> ", True, text_color), (sub_x - 20, y))
            screen.blit(font_sm.render(opt, True, color), (sub_x, y))
