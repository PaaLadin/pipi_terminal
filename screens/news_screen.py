import pygame
import os

NEWS_TXT = "/home/pi/pipi_terminal/news.txt"

def draw(screen, fonts, config_settings, text_color, base_color, nav_focus, news_cursor=0):
    font_md = fonts["md"]
    font_sm = fonts["sm"]
    
    # Вычисляем текущую страницу (0-6: стр 1, 7-13: стр 2, 14-20: стр 3)
    current_page = news_cursor // 7
    total_pages = 3  # Фиксировано 3 страницы под максимум 21 новость
    
    header_str = f"--- SovIntel NEWS NETWORKS FEED [Page {current_page + 1}/{total_pages}] ---"
    header_surf = font_md.render(header_str, True, text_color)
    screen.blit(header_surf, (50, 70))
    
    news_items = []
    if os.path.exists(NEWS_TXT):
        try:
            with open(NEWS_TXT, "r", encoding="utf-8") as f:
                for line in f:
                    if "|" in line:
                        parts = line.strip().split("|", 1)
                        news_items.append({"title": parts[0].strip(), "lead": parts[1].strip()})
        except:
            pass
            
    if not news_items:
        news_items.append({
            "title": "[SYSTEM] No news feed found",
            "lead": "Terminal is isolated."
        })
        
    if news_cursor >= len(news_items):
        news_cursor = max(0, len(news_items) - 1)
        
    split_x = 510
    pygame.draw.line(screen, (int(text_color[0]*0.2), int(text_color[1]*0.2), int(text_color[2]*0.2)), (split_x, 130), (split_x, 460), 1)
    
    # Проблема 4: Фильтруем вывод новостей, отображая только 7 штук для текущей страницы
    start_idx = current_page * 7
    end_idx = start_idx + 7
    page_items = news_items[start_idx:end_idx]
    
    for relative_idx, item in enumerate(page_items):
        absolute_idx = start_idx + relative_idx
        y_pos = 140 + (relative_idx * 45)
        
        if y_pos > 440:
            break
            
        if nav_focus == "content" and news_cursor == absolute_idx:
            scr_color = base_color
            screen.blit(font_sm.render("> ", True, base_color), (30, y_pos))
        else:
            scr_color = text_color
            
        title_text = item["title"]
        if len(title_text) > 38:
            title_text = title_text[:35] + "..."
        title_surf = font_sm.render(title_text, True, scr_color)
        screen.blit(title_surf, (50, y_pos))
        
    # Правая панель расширенного описания для выбранной новости
    if news_cursor < len(news_items):
        selected_item = news_items[news_cursor]
        lead_text = selected_item["lead"]
        lead_x = split_x + 20
        lead_y = 140
        max_width = 1024 - lead_x - 40
        
        lbl_lead_header = font_sm.render("--- EXTENDED SUMMARY ---", True, base_color)
        screen.blit(lbl_lead_header, (lead_x, lead_y))
        lead_y += 35
        
        clean_text = lead_text.replace("[BR]", "\n").replace("[NEWLINE]", "\n").replace("\\n", "\n")
        raw_lines = clean_text.split("\n")
        base_font_height = font_sm.get_linesize()
        qr_step = int(base_font_height * 0.95)
        
        for paragraph in raw_lines:
            if lead_y > 450:
                break
            if not paragraph:
                continue
                
            is_qr_line = any(char in paragraph for char in ["▀", "▄", "█"])
            if is_qr_line:
                qr_line = paragraph
                qr_surf = font_sm.render(qr_line, True, text_color)
                screen.blit(qr_surf, (lead_x, lead_y))
                lead_y += qr_step
            else:
                words = paragraph.split(" ")
                current_line = ""
                for word in words:
                    test_line = current_line + " " + word if current_line else word
                    test_surf = font_sm.render(test_line, True, text_color)
                    if test_surf.get_width() > max_width:
                        if lead_y < 450:
                            screen.blit(font_sm.render(current_line, True, text_color), (lead_x, lead_y))
                            lead_y += 26
                        current_line = word
                    else:
                        current_line = test_line
                if current_line and lead_y < 450:
                    screen.blit(font_sm.render(current_line, True, text_color), (lead_x, lead_y))
                    lead_y += 26
