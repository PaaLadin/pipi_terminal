import pygame
import os
import math
import time
from datetime import datetime

def draw_PiPi_Boy_corners(surface, color, rect, line_len=15, thickness=2):
    """Отрисовка аутентичных угловых полурамок в стиле интерфейса PiPi-Boy"""
    x, y, w, h = rect
    pygame.draw.line(surface, color, (x, y), (x + line_len, y), thickness)
    pygame.draw.line(surface, color, (x, y), (x, y + line_len), thickness)
    pygame.draw.line(surface, color, (x + w, y), (x + w - line_len, y), thickness)
    pygame.draw.line(surface, color, (x + w, y), (x + w, y + line_len), thickness)
    pygame.draw.line(surface, color, (x, y + h), (x + line_len, y + h), thickness)
    pygame.draw.line(surface, color, (x, y + h), (x, y + h - line_len), thickness)
    pygame.draw.line(surface, color, (x + w, y + h), (x + w - line_len, y + h), thickness)
    pygame.draw.line(surface, color, (x + w, y + h), (x + w, y + h - line_len), thickness)

def draw(screen, fonts, stations, current_station_idx, is_paused, weather_data, text_color, news_scroll_x=1024):
    """Переработанный интерфейс главного дашборда в стиле SovIntel PiPi-Boy"""
    now = datetime.now()
    font_bg = fonts["bg"]
    font_md = fonts["md"]
    font_sm = fonts["sm"]
    dim_grid_color = (int(text_color[0]*0.15), int(text_color[1]*0.15), int(text_color[2]*0.15))
    
    str_time = now.strftime("%H:%M:%S")
    str_date = now.strftime("%d.%m.%Y")
    str_day_of_week = now.strftime("%A").upper()
    
    screen.blit(font_bg.render(str_time, True, text_color), (60, 65))
    screen.blit(font_md.render(f"{str_day_of_week} | {str_date}", True, text_color), (360, 75))
    
    alarm_time = "NOT SET"
    if os.path.exists("/home/pi/pipi_terminal/config.json"):
        import json
        try:
            with open("/home/pi/pipi_terminal/config.json", "r") as cjf:
                cfg = json.load(cjf)
                if cfg.get("alarm_enabled", False):
                    alarm_time = cfg.get("alarm_time", "07:00")
        except: pass
    
    alarm_surf = font_md.render(f"ALARM: {alarm_time}", True, text_color)
    screen.blit(alarm_surf, (700, 75))
    draw_PiPi_Boy_corners(screen, text_color, (45, 55, 934, 65), line_len=20, thickness=2)
    
    audio_rect = (45, 140, 450, 200)
    draw_PiPi_Boy_corners(screen, text_color, audio_rect, line_len=15, thickness=2)
    screen.blit(font_md.render(">> AUDIO RECEIVER UNIT", True, text_color), (60, 150))
    station_name = stations[current_station_idx]['name']
    
    is_connected = True
    if not is_connected:
        screen.blit(font_sm.render(f"STATION: {station_name}", True, dim_grid_color), (70, 185))
        lbl_status = font_md.render("[NO CONNECTION]", True, text_color)
        if int(time.time() * 2) % 2 == 0:
            screen.blit(lbl_status, (150, 230))
    elif is_paused:
        screen.blit(font_sm.render(f"STATION: {station_name}", True, text_color), (70, 185))
        pygame.draw.rect(screen, text_color, (230, 220, 12, 35))
        pygame.draw.rect(screen, text_color, (252, 220, 12, 35))
        screen.blit(font_sm.render("|| RECEIVER PAUSED", True, text_color), (70, 290))
    else:
        screen.blit(font_sm.render(f"STATION: {station_name}", True, text_color), (70, 185))
        wave_points = []
        t_shift = time.time() * 15
        for x_i in range(80, 450, 4):
            y_i = 240 + int(18 * math.sin(x_i * 0.09 + t_shift) * math.cos(x_i * 0.02 - t_shift * 0.3))
            wave_points.append((x_i, y_i))
        if len(wave_points) > 1:
            pygame.draw.lines(screen, text_color, False, wave_points, 2)
        screen.blit(font_sm.render("STATUS: SIGNAL ALIVE / 128KBPS", True, text_color), (70, 290))

    weather_rect = (525, 140, 454, 200)
    draw_PiPi_Boy_corners(screen, text_color, weather_rect, line_len=15, thickness=2)
    screen.blit(font_md.render(">> METEO DATA MATRICES", True, text_color), (540, 150))
    
    w_code = 113
    temp_str = "N/A"
    wind_str = "N/A"
    humidity_str = "N/A"
    
    for line in weather_data:
        line = line.strip()
        if "CODE:" in line:
            try: w_code = int(line.split(":", 1)[1].strip())
            except: pass
        elif "TEMP:" in line:
            temp_str = line.split(":", 1)[1].strip()
        elif "WIND:" in line:
            wind_str = line.split(":", 1)[1].strip()
        elif "HUMIDITY:" in line:
            humidity_str = line.split(":", 1)[1].strip()
            
    weather_conditions = {
        113: "CLEAR SKY", 116: "PARTLY CLOUDY", 119: "CLOUDY STATUS", 122: "OVERCAST",
        143: "HEAVY FOG", 248: "DENSE MIST", 260: "FREEZING FOG",
        293: "LIGHT RAIN", 296: "PATCHY RAIN", 302: "HEAVY RAIN", 308: "THERMAL STORMS",
        323: "LIGHT SNOW", 332: "MODERATE SNOW", 338: "BLIZZARD CONDITIONS", 395: "NUCLEAR WINTER"
    }
    condition_text = weather_conditions.get(w_code, "NOMINAL")
    
    screen.blit(font_sm.render(f"THERMAL SENSOR:   {temp_str}", True, text_color), (550, 195))
    screen.blit(font_sm.render(f"WIND SPEED:       {wind_str}", True, text_color), (550, 225))
    screen.blit(font_sm.render(f"AIR MOISTURE:     {humidity_str}", True, text_color), (550, 255))
    
    cond_surf = font_md.render(f"CONDITION: {condition_text}", True, text_color)
    screen.blit(cond_surf, (550, 290))

    marquee_box_rect = pygame.Rect(45, 375, 934, 60)
    pygame.draw.rect(screen, text_color, marquee_box_rect, 2, border_radius=8)
    screen.blit(font_sm.render(" SATELLITE RNN STREAM ", True, text_color, (5, 10, 5)), (65, 366))
    
    by_news, steam_news, all_news = [], [], []
    news_file_path = "/home/pi/pipi_terminal/news.txt"
    if os.path.exists(news_file_path):
        try:
            with open(news_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "|" in line:
                        title = line.strip().split("|", 1)[0].strip()
                        title_upper = title.upper()
                        if "STEAM" in title_upper or "[STEAM]" in title_upper:
                            steam_news.append(title)
                        elif "BY" in title_upper or "БЕЛАРУСЬ" in title_upper or "[BY]" in title_upper:
                            by_news.append(title)
                        else:
                            all_news.append(title)
        except: pass

    ordered_news = []
    max_len = max(len(by_news), len(steam_news), len(all_news))
    for i in range(max_len):
        if i < len(by_news): ordered_news.append(by_news[i])
        if i < len(all_news): ordered_news.append(all_news[i])
        if i < len(steam_news): ordered_news.append(steam_news[i])
        
    if not ordered_news:
        ordered_news = ["SovIntel ONLINE", "SATELLITE DOWNLINK STABLE", "ALL MATRICES GREEN"]
        
    separator = "   ***   "
    marquee_y = 393
    
    current_clip = screen.get_clip()
    screen.set_clip(pygame.Rect(55, marquee_y, 914, 30))
    
    current_x = news_scroll_x
    total_marquee_width = 0
    
    for title in ordered_news:
        text_surf = font_sm.render(title, True, text_color)
        screen.blit(text_surf, (current_x, marquee_y))
        current_x += text_surf.get_width()
        total_marquee_width += text_surf.get_width()
        
        sep_surf = font_sm.render(separator, True, text_color)
        screen.blit(sep_surf, (current_x, marquee_y))
        current_x += sep_surf.get_width()
        total_marquee_width += sep_surf.get_width()
        
    screen.set_clip(current_clip)
    
    global_tracker_path = "/home/pi/pipi_terminal/.marquee_width"
    try:
        with open(global_tracker_path, "w") as f:
            f.write(str(total_marquee_width))
    except: pass
