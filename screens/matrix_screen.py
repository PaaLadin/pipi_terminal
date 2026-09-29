# ====================================================================
# SovIntel OS HIGH-DENSITY ULTRA-SMOOTH MATRIX SCREENSAVER
# ====================================================================
import random
import pygame

# Глобальные контейнеры структуры цифрового дождя
matrix_font = None
matrix_cols = 0
matrix_drops = []
tick_counter = 0  

# Кэш пред-отрендеренных символов (Высокая производительность для RPi 3B)
char_cache = {"head": [], "fade": [[] for _ in range(10)]}

def init_matrix(width, height, base_color):
    """Инициализация плотного попиксельного дождя и пред-рендеринг кэша"""
    global matrix_font, matrix_cols, matrix_drops, char_cache
    
    matrix_font = pygame.font.SysFont("Courier", 16, bold=True)
    
    # Возвращаем каноничную высокую плотность оригинальной Матрицы (шаг 16 пикселей)
    matrix_cols = width // 16 
    matrix_drops = []
    
    char_cache["head"] = []
    char_cache["fade"] = [[] for _ in range(10)]
    
    # Разложение кортежа цвета на независимые RGB каналы для защиты от крашей
    r, g, b = base_color
    
    # Расчет "мягкого лидера" под текущий диммер ночного режима
    brightness_factor = sum(base_color) / (3 * 255) if sum(base_color) > 0 else 0.05
    head_white = (
        int(200 * brightness_factor + r * 0.2),
        int(255 * brightness_factor + g * 0.2),
        int(200 * brightness_factor + b * 0.2)
    )
    head_white = tuple(max(0, min(255, c)) for c in head_white)
    
    # Наполняем кэш для всех печатных ASCII символов
    for code in range(33, 127):
        ch = chr(code)
        char_cache["head"].append(matrix_font.render(ch, True, head_white))
        
        for step in range(10):
            fade_factor = ((10 - step) / 10) ** 1.8  # Мягкое ретро-затухание
            dimmed = (
                int(r * fade_factor),
                int(g * fade_factor),
                int(b * fade_factor)
            )
            char_cache["fade"][step].append(matrix_font.render(ch, True, dimmed))

    # Инициализация параметров попиксельного скольжения БЕЗ мутаций в будущем
    for i in range(matrix_cols):
        max_rows = height // 16 + 5
        matrix_drops.append({
            "y_pos": float(-random.randint(0, height)),   # Позиция головы в ПИКСЕЛЯХ
            "speed": random.uniform(1.2, 2.8),            # Комфортная плавная скорость
            "length": random.randint(12, 26),             # Количество символов в хвосте
            "chars": [random.randint(0, 93) for _ in range(max_rows)]  # Фиксированная матрица букв
        })

# ====================================================================
# БЛОК 3: ВЫСОКОПРОИЗВОДИТЕЛЬНЫЙ МОНОЛИТНЫЙ ЦИКЛ ОТРИСОВКИ
# ====================================================================
def draw(screen, width, height, text_color):
    """
    Высокопроизводительный цикл попиксельного рендеринга цифрового дождя.
    Исключает дёрганность за счёт полного удаления случайных мутаций из цикла.
    """
    global matrix_drops
    
    # Автоинициализация кэша при первом старте или смене темы/диммера
    if not matrix_drops:
        init_matrix(width, height, text_color)

    cell_h = 16
    rows_on_screen = height // cell_h

    # Чистый цикл отрисовки капель без единой математической проверки
    for i, drop in enumerate(matrix_drops):
        x_pos = i * 16
        
        current_y_pixels = drop["y_pos"]
        head_row = int(current_y_pixels // cell_h)
        pixel_offset = int(current_y_pixels % cell_h)

        # Скоростной перенос готовых текстур из ОЗУ на экран em713
        for j in range(drop["length"]):
            char_row = head_row - j
            
            if char_row < 0 or char_row > rows_on_screen + 1:
                continue
                
            char_idx = drop["chars"][char_row % len(drop["chars"])]
            draw_y = char_row * cell_h + pixel_offset

            if j == 0:
                # --- ДЕЛИКАТНЫЙ БЕЛЫЙ ЛИДЕР ---
                char_surf = char_cache["head"][char_idx]
            else:
                # --- ЗАТУХАЮЩИЙ ХВОСТ ---
                step = int((j / drop["length"]) * 10)
                step = max(0, min(9, step))
                char_surf = char_cache["fade"][step][char_idx]

            screen.blit(char_surf, (x_pos, draw_y))

        # Плавное смещение капли вниз по пикселям
        drop["y_pos"] += drop["speed"]

        # Безопасный перезапуск ушедшего потока кода
        total_drop_height_pixels = drop["length"] * cell_h
        if drop["y_pos"] - total_drop_height_pixels > height:
            drop["y_pos"] = float(-random.randint(0, 150))
            drop["speed"] = random.uniform(1.2, 2.8)
            drop["length"] = random.randint(12, 26)
