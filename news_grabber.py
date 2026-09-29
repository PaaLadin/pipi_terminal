# ==============================================================================
# SovIntel INDUSTRIES TERMINAL OS v5.4 — 21 ITEMS MAX NEWS MONITOR
# ==============================================================================

import urllib.request
import os
import sys
if os.path.exists("/home/pi/pipi_terminal/.deep_sleep"):
    sys.exit(0)  # Защита процессора: мгновенный выход во время сна станции
import re

try:
    import qrcode
    HAS_QR = True
except ImportError:
    HAS_QR = False

NEWS_TXT = "/home/pi/pipi_terminal/news.txt"
BLACKLIST_FILE = "/home/pi/pipi_terminal/blacklist.txt"
WHITELIST_FILE = "/home/pi/pipi_terminal/whitelist.txt"


def generate_compact_qr(url):
    """Генерация компактного QR-кода псевдографикой без смещения границ."""
    if not HAS_QR or not url:
        return ""
    try:
        clean_url = url.strip().lower()
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=0,
        )
        qr.add_data(clean_url)
        qr.make(fit=True)
        
        matrix = qr.get_matrix()
        lines = []
        
        height = len(matrix)
        width = len(matrix[0])
        
        for y in range(0, height, 2):
            line = ""
            for x in range(width):
                top = matrix[y][x]
                bottom = matrix[y + 1][x] if (y + 1) < height else False
                
                if top and bottom:
                    line += "█"
                elif top and not bottom:
                    line += "▀"
                elif not top and bottom:
                    line += "▄"
                else:
                    line += " "
            lines.append(line)
            
        return "[BR]".join(lines)
    except Exception as e:
        print(f"QR Generation error: {e}")
        return ""


def extract_url(text):
    """Извлечение ссылки из описания для генерации QR-кода."""
    if not text:
        return ""
    match = re.search(r'https?://[^\s<>"]+', text)
    return match.group(0) if match else ""


def load_list_from_file(file_path):
    """Загрузка черных и белых списков ключевых слов."""
    items = []
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    items.append(line.lower())
    return items


def clean_html(text):
    """Очистка тегов HTML и спецсимволов."""
    if not text:
        return ""
    text = text.replace('<![CDATA[', '').replace(']]>', '')
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&apos;', "'").replace('&#39;', "'").replace('&nbsp;', ' ')
    text = text.replace('&#171;', '«').replace('&#187;', '»')
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    return re.sub(r'\s+', ' ', text).strip()


def check_news_against_lists(title, desc, blacklist, whitelist):
    """Проверка новости по фильтрам whitelist/blacklist."""
    combined = (title + " " + desc).lower()
    for w_word in whitelist:
        if w_word in combined:
            return True, True
    for b_word in blacklist:
        if b_word in combined:
            return False, False
    return True, False


def regex_parse_rss(xml_text, blacklist, whitelist, require_steam_only=False):
    """Парсинг структуры RSS/XML."""
    items = []
    blocks = re.findall(r'<(?:item|ITEM)>(.*?)</(?:item|ITEM)>', xml_text, re.DOTALL)
    if not blocks:
        blocks = re.findall(r'<(?:entry|ENTRY)>(.*?)</(?:entry|ENTRY)>', xml_text, re.DOTALL)
    
    for block in blocks:
        t_match = re.search(r'<(?:title|TITLE)>(.*?)</(?:title|TITLE)>', block, re.DOTALL)
        d_match = re.search(r'<(?:description|DESCRIPTION|summary|SUMMARY)>(.*?)</(?:description|DESCRIPTION|summary|SUMMARY)>', block, re.DOTALL)
        
        if t_match:
            title = clean_html(t_match.group(1))
            desc = clean_html(d_match.group(1)) if d_match else "Официальная сводка SovIntel."
            
            is_valid, is_whitelisted = check_news_against_lists(title, desc, blacklist, whitelist)
            if not is_valid:
                continue
            if require_steam_only and not is_whitelisted:
                continue

            if require_steam_only:
                url = extract_url(desc) or extract_url(block)
                if url:
                    qr_code = generate_compact_qr(url)
                    if qr_code:
                        desc = qr_code
                    else:
                        desc = "Раздача в Steam."
                else:
                    desc = "Раздача в Steam."

            if title:
                items.append((title, desc))
    return items


def fetch_feed(url, prefix, blacklist, whitelist, max_items=7, require_steam_only=False):
    """Получение новостей из фида (до 7 штук на каждый канал)."""
    items = []
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) SovIntelNewsMonitor/5.4'}
        )
        with urllib.request.urlopen(req, timeout=7) as response:
            raw_data = response.read().decode('utf-8', errors='ignore')
            parsed = regex_parse_rss(raw_data, blacklist, whitelist, require_steam_only=require_steam_only)
            for title, desc in parsed[:max_items]:
                items.append({"title": f"{prefix} {title}", "lead": desc})
    except Exception as e:
        print(f"Feed error [{url}]: {e}")
    return items


def main():
    print("Starting SovIntel High-Substance News Monitor v5.4...")
    blacklist = load_list_from_file(BLACKLIST_FILE)
    whitelist = load_list_from_file(WHITELIST_FILE)
    
    all_news = []
    # Запрашиваем до 7 новостей с каждого направления
    all_news.extend(fetch_feed("https://www.belta.by/rss/allnews.rss", "[BY]", blacklist, whitelist, 7))
    
    world = fetch_feed("https://www.interfax.ru/rss.asp", "[ALL]", blacklist, whitelist, 7)
    if not world:
        world = fetch_feed("https://rssexport.rbc.ru/rbcnews/news/20/full.rss", "[ALL]", blacklist, whitelist, 7)
    all_news.extend(world)

    steam = fetch_feed("https://freesteam.ru/feed/", "[STEAM]", blacklist, whitelist, 7, require_steam_only=True)
    if not steam:
        steam = fetch_feed("https://rbkgames.com/rss/news/", "[STEAM]", blacklist, whitelist, 7, require_steam_only=True)
    all_news.extend(steam)

    # Строгое ограничение: максимум 21 новость
    all_news = all_news[:21]

    if not all_news:
        all_news = [
            {"title": "[SovIntel OS] Автономный режим терминала активен", "lead": "Глобальная сеть недоступна."},
            {"title": "[BY] Сводка атмосферных условий", "lead": "Данные об атмосфере обновляются автономно."},
            {"title": "[STEAM] Монитор халявы Steam", "lead": "В настоящий момент 100% раздач в Steam не обнаружено."}
        ]

    output_lines = []
    for item in all_news:
        t = item["title"].replace("|", "-").replace("\n", " ").replace("\r", " ")
        l = item["lead"].replace("|", "-").replace("\n", " ").replace("\r", " ")
        output_lines.append(f"{t}|{l}")

    with open(NEWS_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print(f"Successfully compiled {len(output_lines)} news entries.")

if __name__ == "__main__":
    main()
