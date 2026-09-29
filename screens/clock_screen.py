import pygame
def draw_bell_icon(surface, color, pos):
    x, y = pos
    pygame.draw.line(surface, color, (x, y + 40), (x + 40, y + 40), 4)
    pygame.draw.line(surface, color, (x + 6, y + 20), (x + 6, y + 40), 3)
    pygame.draw.line(surface, color, (x + 34, y + 20), (x + 34, y + 40), 3)
    pygame.draw.line(surface, color, (x + 6, y + 20), (x + 20, y + 6), 3)
    pygame.draw.line(surface, color, (x + 34, y + 20), (x + 20, y + 6), 3)
    pygame.draw.circle(surface, color, (x + 20, y + 44), 3)
    pygame.draw.circle(surface, color, (x + 20, y + 4), 2)


from datetime import datetime, timedelta

def draw(screen, fonts, config_settings, text_color):
    """Отремонтированный экран часов с Юникод-иконкой будильника вместо пикселей"""
    now = datetime.now()
    font_huge = fonts["huge"]
    font_md = fonts["md"]
    font_sm = fonts["sm"]
    
    str_large_time = now.strftime("%H:%M:%S")
    str_date = now.strftime("%d.%m.%Y")
    str_day = now.strftime("%A").upper()
    
    frame_x, frame_y = 45, 90
    frame_w, frame_h = 934, 260
    frame_thickness = 4
    
    # Крупный циферблат
    raw_time_surf = font_huge.render(str_large_time, True, text_color)
    large_time_surf = pygame.transform.scale_by(raw_time_surf, 1.6)
    
    time_x = frame_x + (frame_w - large_time_surf.get_width()) // 2
    time_y = frame_y + (frame_h - large_time_surf.get_height()) // 2 + 15
    screen.blit(large_time_surf, (time_x, time_y))
    
    # Рамка фрейма
    pygame.draw.line(screen, text_color, (frame_x, frame_y), (frame_x, frame_y + frame_h), frame_thickness)
    pygame.draw.line(screen, text_color, (frame_x + frame_w, frame_y), (frame_x + frame_w, frame_y + frame_h), frame_thickness)
    pygame.draw.line(screen, text_color, (frame_x, frame_y + frame_h), (frame_x + frame_w, frame_y + frame_h), frame_thickness)
    
    # Баннер даты в правом углу
    banner_text = f"[ {str_day} | {str_date} ]"
    banner_surf = font_md.render(banner_text, True, text_color)
    banner_x = frame_x + frame_w - banner_surf.get_width() - 40
    
    pygame.draw.line(screen, text_color, (frame_x, frame_y), (banner_x - 12, frame_y), frame_thickness)
    pygame.draw.line(screen, text_color, (banner_x + banner_surf.get_width() + 12, frame_y), (frame_x + frame_w, frame_y), frame_thickness)
    screen.blit(banner_surf, (banner_x, frame_y - banner_surf.get_height() // 2))

    # 4. Обработка и рендер обновленного блока обратного отсчета (COUNTDOWN)
    is_alarm_enabled = config_settings.get("alarm_enabled", True)
    alarm_time_str = config_settings.get("alarm_time", "07:00")
    
    if is_alarm_enabled:
        try:
            alarm_hour, alarm_min = map(int, alarm_time_str.split(":"))
            alarm_target = now.replace(hour=alarm_hour, minute=alarm_min, second=0, microsecond=0)
            if alarm_target < now:
                alarm_target += timedelta(days=1)
                
            time_left = alarm_target - now
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            # Позиционирование измененного блока: левее и ниже основного фрейма
            box_x, box_y = 65, frame_y + frame_h + 30
            box_w, box_h = 420, 90
            
            # Родная угловатая SovIntel-рамка со скошенными углами по бокам
            pygame.draw.line(screen, text_color, (box_x + 10, box_y), (box_x + box_w - 10, box_y), 2)
            pygame.draw.line(screen, text_color, (box_x + 10, box_y + box_h), (box_x + box_w - 10, box_y + box_h), 2)
            pygame.draw.line(screen, text_color, (box_x, box_y + 10), (box_x + 10, box_y), 2)
            pygame.draw.line(screen, text_color, (box_x, box_y + box_h - 10), (box_x + 10, box_y + box_h), 2)
            pygame.draw.line(screen, text_color, (box_x + box_w, box_y + 10), (box_x + box_w - 10, box_y), 2)
            pygame.draw.line(screen, text_color, (box_x + box_w, box_y + box_h - 10), (box_x + box_w - 10, box_y + box_h), 2)
            pygame.draw.line(screen, text_color, (box_x, box_y + 10), (box_x, box_y + box_h - 10), 2)
            pygame.draw.line(screen, text_color, (box_x + box_w, box_y + 10), (box_x + box_w, box_y + box_h - 10), 2)
            
            # Геометрическая отрисовка крупного колокольчика
            draw_bell_icon(screen, text_color, (box_x + 20, box_y + 22))
            
            # Текстовые параметры для вывода контента справа от иконки
            content_left_x = box_x + 95
            text_area_w = box_w - 115
            
            # Название блока: строго "COUNTDOWN", центрировано по ширине текстовой зоны
            lbl_title = font_sm.render("COUNTDOWN", True, text_color)
            title_x = content_left_x + (text_area_w - lbl_title.get_width()) // 2
            screen.blit(lbl_title, (title_x, box_y + 15))
            
            # Крупный бордовый/розовый таймер, смещенный строго ПОД название
            burgundy_digits = (185, 22, 40)
            str_countdown = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            digits_surf = font_md.render(str_countdown, True, burgundy_digits)
            
            digits_x = content_left_x + (text_area_w - digits_surf.get_width()) // 2
            screen.blit(digits_surf, (digits_x, box_y + 44))
            
        except Exception:
            pass
