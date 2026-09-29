import pygame
import datetime

# ==============================================================================
# МОДУЛЬ ВКЛАДКИ 4: МЕТЕОСТАНЦИЯ С АВТОМОБИЛЬНОЙ ПАНЕЛЬЮ И МУЛЬТИ-ОСЦИЛЛОГРАФОМ
# ==============================================================================

def draw_rounded_rect(surface, color, rect, radius, width=0):
    """Отрисовка рамок ламп со скруглением"""
    pygame.draw.rect(surface, color, rect, width, border_radius=radius)

def draw(screen, fonts, weather_data, text_color, base_color, nav_focus, graph_idx=0, day_offset=0):
    """Цикл отрисовки метеоданных, карты и 6 статусных индикаторов с поддержкой 5 графиков и 3 дней"""
    font_md = fonts["md"]
    font_sm = fonts["sm"]
    font_bg = fonts["bg"]

    # Заголовки экрана SovIntel
    screen.blit(font_md.render("--- AUTOMATED METEOROLOGICAL COMPLEX ---", True, text_color), (50, 70))
    screen.blit(font_md.render("REGIONAL TARGET: BREST, BY", True, text_color), (50, 110))

    w_code = 113
    alert_status = "NONE"
    parsed_metrics = {}
    history_points = []
    forecast_points = []

    f_prefix = f"F{day_offset}_"

    for line in weather_data:
        line = line.strip()
        if not line:
            continue
        if "CODE:" in line:
            try: 
                parts = line.split(":", 1)
                w_code = int(parts[1].strip())
            except: pass
            continue
        if "PREDICT:" in line:
            try:
                parts = line.split(":", 1)
                alert_status = parts[1].strip()
            except: pass
            continue
        if day_offset == 0 and "H_" in line:
            try:
                t_time, t_val = line.replace("H_", "").split("=")
                packs = t_val.strip().split("|")
                val_to_graph = float(packs[graph_idx])
                history_points.append((t_time.strip(), val_to_graph))
            except: pass
            continue
        if f_prefix in line:
            try:
                t_time, t_val = line.replace(f_prefix, "").split("=")
                packs = t_val.strip().split("|")
                val_to_graph = float(packs[graph_idx])
                forecast_points.append((t_time.strip(), val_to_graph))
            except: pass
            continue
        if ":" in line:
            try:
                parts = line.split(":", 1)
                parsed_metrics[parts[0].strip()] = parts[1].strip()
            except: pass

    metrics_order = ["TEMP", "WIND", "HUMIDITY", "BAROMETER", "UV INDEX"]
    for idx, key in enumerate(metrics_order):
        val = parsed_metrics.get(key, "N/A")
        if nav_focus == "content" and graph_idx == idx:
            scr_color = base_color
            screen.blit(font_sm.render("> ", True, base_color), (30, 160 + (idx * 38)))
        else:
            scr_color = text_color
        screen.blit(font_sm.render(f"{key}:", True, scr_color), (50, 160 + (idx * 38)))
        screen.blit(font_sm.render(val, True, scr_color), (240, 160 + (idx * 38)))

    if alert_status != "NONE":
        status_surf = font_sm.render(f"WARNING: EXPECTED {alert_status}", True, base_color)
    else:
        status_surf = font_sm.render("STATUS: SYSTEMS NOMINAL / TELEMETRY LIVE", True, text_color)
    screen.blit(status_surf, (50, 360))

    lamp_clear = (w_code == 113)
    lamp_cloudy = (w_code == 116 or w_code == 119 or w_code == 122)
    lamp_fog = (w_code == 143 or w_code == 248 or w_code == 260)
    lamp_rain = ((w_code >= 293 and w_code <= 308) or (w_code >= 353 and w_code <= 359))
    lamp_snow = ((w_code >= 323 and w_code <= 338) or (w_code >= 368 and w_code <= 371) or w_code == 395)
    lamp_thunder = (w_code >= 386 and w_code <= 392)
    
    if w_code == 176 or w_code == 182 or w_code == 185 or w_code == 281 or w_code == 284 or w_code == 311:
        lamp_rain = True
        lamp_snow = True

    lamps_config = [
        {"name": "CLEAR", "active": lamp_clear},
        {"name": "CLOUDS", "active": lamp_cloudy},
        {"name": "FOG", "active": lamp_fog},
        {"name": "RAIN", "active": lamp_rain},
        {"name": "SNOW", "active": lamp_snow},
        {"name": "STORM", "active": lamp_thunder}
    ]

    box_w, box_h = 75, 45
    start_x, start_y = 50, 480
    for i, lamp in enumerate(lamps_config):
        x = start_x + (i * (box_w + 15))
        rect_coord = (x, start_y, box_w, box_h)
        if lamp["active"]:
            box_color = base_color
            text_color_lamp = (4, 20, 4)
            fill_box = 0
        else:
            box_color = (int(text_color[0]*0.15), int(text_color[1]*0.15), int(text_color[2]*0.15))
            text_color_lamp = box_color
            fill_box = 2

        if fill_box == 0: draw_rounded_rect(screen, box_color, rect_coord, 8, 0)
        else: draw_rounded_rect(screen, box_color, rect_coord, 8, 2)
        txt_surf = font_sm.render(lamp["name"], True, text_color_lamp)
        screen.blit(txt_surf, (x + (box_w - txt_surf.get_width()) // 2, start_y + (box_h - txt_surf.get_height()) // 2))

    if nav_focus == "tabs":
        map_points = [
            (624, 290), (655, 290), (689, 270), (696, 239), (722, 222), (719, 198),
            (738, 189), (772, 168), (806, 181), (810, 195), (827, 188), (858, 201),
            (861, 226), (854, 241), (874, 276), (887, 286), (885, 296), (906, 306),
            (915, 320), (903, 332), (877, 330), (871, 335), (879, 353), (886, 388),
            (859, 391), (849, 403), (847, 430), (835, 425), (806, 427), (798, 415),
            (786, 424), (774, 416), (749, 415), (714, 402), (682, 398), (658, 399),
            (640, 414), (625, 416), (625, 392), (615, 367), (634, 356), (634, 334),
            (625, 314), (624, 290)
        ]
        pygame.draw.lines(screen, text_color, True, map_points, 2)
        screen.blit(font_sm.render("x [BREST]", True, base_color), (642, 363))
    else:
        graph_x, graph_y, graph_w, graph_h = 580, 150, 410, 250
        pygame.draw.rect(screen, (int(text_color[0]*0.3), int(text_color[1]*0.3), int(text_color[2]*0.3)), (graph_x, graph_y, graph_w, graph_h), 1)
        
        zero_y = graph_y + graph_h // 2
        pygame.draw.line(screen, (int(text_color[0]*0.15), int(text_color[1]*0.15), int(text_color[2]*0.15)), (graph_x, zero_y), (graph_x + graph_w, zero_y), 1)
        
        graph_titles = ["TEMPERATURE TREND", "WIND SPEED TREND", "AIR HUMIDITY TREND", "ATMOSPHERIC PRESSURE TREND", "ULTRAVIOLET INDEX TREND"]
        graph_suffixes = ["°C", " m/s", "%", " mmHg", " UV"]
        graph_scales = [5.0, 8.0, 2.0, 15.0, 20.0]
        day_labels = ["TODAY", "TOMORROW", "DAY AFTER"]

        title_text = graph_titles[graph_idx]
        suffix = graph_suffixes[graph_idx]
        y_scale = graph_scales[graph_idx]
        current_day_name = day_labels[day_offset]

        current_val = 0.0
        raw_temp = parsed_metrics.get("TEMP", "0").split("°")[0]
        raw_wind = parsed_metrics.get("WIND", "0").split(" ")[0]
        raw_hum = parsed_metrics.get("HUMIDITY", "0").replace("%", "")
        raw_baro = parsed_metrics.get("BAROMETER", "760").split(" ")[0]
        raw_uv = parsed_metrics.get("UV INDEX", "0")

        try:
            if graph_idx == 0: current_val = float(raw_temp)
            elif graph_idx == 1: current_val = float(raw_wind)
            elif graph_idx == 2: current_val = float(raw_hum)
            elif graph_idx == 3: current_val = float(raw_baro)
            elif graph_idx == 4: current_val = float(raw_uv)
        except: pass

        screen.blit(font_sm.render(f"--- {current_day_name} | {title_text} ---", True, text_color), (graph_x, graph_y - 30))

        x_start = graph_x + 30
        x_end = graph_x + graph_w - 30
        x_span = x_end - x_start

        dim_color = (int(text_color[0]*0.4), int(text_color[1]*0.4), int(text_color[2]*0.4))
        major_ticks = [0, 6, 12, 18, 24]
        for tick in major_ticks:
            tx = x_start + int((tick / 24.0) * x_span)
            pygame.draw.line(screen, dim_color, (tx, graph_y + graph_h), (tx, graph_y + graph_h + 10), 1)
            lbl_tick = font_sm.render(f"{tick:02d}", True, dim_color)
            screen.blit(lbl_tick, (tx - lbl_tick.get_width()//2, graph_y + graph_h + 14))

        minor_ticks = [3, 9, 15, 21]
        for tick in minor_ticks:
            tx = x_start + int((tick / 24.0) * x_span)
            pygame.draw.line(screen, dim_color, (tx, graph_y + graph_h), (tx, graph_y + graph_h + 5), 1)

        now_dt = datetime.datetime.now()
        now_hour_fraction = now_dt.hour + (now_dt.minute / 60.0)
        now_x = x_start + int((now_hour_fraction / 24.0) * x_span)

        all_pts = []
        for h_time, h_val in history_points:
            try:
                t_parts = h_time.split(":")
                hr = int(t_parts[0]) + (int(t_parts[1]) / 60.0)
                all_pts.append((hr, h_val, False))
            except: pass

        if day_offset == 0:
            all_pts.append((now_hour_fraction, current_val, True))

        for f_time, f_val in forecast_points:
            try:
                t_parts = f_time.split(":")
                hr = int(t_parts[0]) + (int(t_parts[1]) / 60.0)
                if day_offset != 0 or abs(hr - now_hour_fraction) > 0.5:
                    all_pts.append((hr, f_val, False))
            except: pass

        all_pts.sort(key=lambda p: p[0])

        base_val = all_pts[0][1] if len(all_pts) > 0 else current_val
        line_points = []

        for hr, val, is_now in all_pts:
            cx = x_start + int((hr / 24.0) * x_span)
            val_diff = val - base_val
            cy = zero_y - int(val_diff * y_scale)
            line_points.append((cx, cy))

            if not is_now:
                disp_val = int(val) if float(val).is_integer() else round(val, 1)
                lbl = font_sm.render(f"{disp_val}", True, text_color)
                screen.blit(lbl, (cx - lbl.get_width()//2, cy - 20))
                pygame.draw.circle(screen, text_color, (cx, cy), 3.5)
            else:
                pygame.draw.circle(screen, base_color, (cx, cy), 6)

        if len(line_points) > 1:
            pygame.draw.lines(screen, text_color, False, line_points, 2)

        if day_offset == 0:
            disp_curr = int(current_val) if float(current_val).is_integer() else round(current_val, 1)
            lbl_val = font_md.render(f"{disp_curr}{suffix}", True, base_color)
            lbl_now = font_sm.render("NOW", True, base_color)
            lbl_arrow = font_sm.render("⬇", True, base_color)

            y_arrow = graph_y + graph_h - 16
            y_now = y_arrow - 15
            y_val = y_now - 20

            screen.blit(lbl_val, (now_x - lbl_val.get_width()//2, y_val))
            screen.blit(lbl_now, (now_x - lbl_now.get_width()//2, y_now))
            screen.blit(lbl_arrow, (now_x - lbl_arrow.get_width()//2, y_arrow))
