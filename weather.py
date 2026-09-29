import subprocess
import json
import os
from datetime import datetime

import sys
if os.path.exists("/home/pi/pipi_terminal/.deep_sleep"):
    sys.exit(0)  # Станция спит, завершаем процесс для защиты от перегрева

CACHE_DIR = "/home/pi/pipi_terminal"
WEATHER_TXT = os.path.join(CACHE_DIR, "weather.txt")
HISTORY_JSON = os.path.join(CACHE_DIR, "weather_history.json")

def load_history():
    if os.path.exists(HISTORY_JSON):
        try:
            with open(HISTORY_JSON, "r") as f: return json.load(f)
        except Exception: pass
    return []

def save_history(history):
    try:
        with open(HISTORY_JSON, "w") as f: json.dump(history, f, indent=2)
    except Exception: pass

try:
    cmd = "curl -s 'wttr.in/Brest?format=j1'"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)

    if res.returncode == 0 and res.stdout.strip():
        w_data = json.loads(res.stdout.strip())
        current = w_data["current_condition"][0]

        temp = current["temp_C"]
        feels = current["FeelsLikeC"]
        humidity = current["humidity"]
        uv = current["uvIndex"]
        w_code = current["weatherCode"]
        wind_dir = current["winddir16Point"]
        wind_ms = round(float(current["windspeedKmph"]) / 3.6, 1)
        press_mm = int(float(current["pressure"]) * 0.75006)

        # 1. Логирование текущей истории
        now_str = datetime.now().strftime("%H:%M")
        history = load_history()
        history.append({
            "time": now_str, 
            "temp": str(temp),
            "wind": str(wind_ms),
            "hum": str(humidity),
            "baro": str(press_mm),
            "uv": str(uv)
        })
        if len(history) > 4:
            history.pop(0)
        save_history(history)

        forecast_entries = []
        upcoming_precipitation = "NONE"

        # 2. Перебираем ровно 3 дня (0: сегодня, 1: завтра, 2: послезавтра)
        if "weather" in w_data and isinstance(w_data["weather"], list):
            for day_idx in range(min(3, len(w_data["weather"]))):
                day_entry = w_data["weather"][day_idx]
                if "hourly" in day_entry:
                    for hour_entry in day_entry["hourly"]:
                        h_time_raw = int(hour_entry["time"])
                        h_time = h_time_raw // 100
                        
                        f_temp = hour_entry["tempC"]
                        f_wind = round(float(hour_entry["windspeedKmph"]) / 3.6, 1)
                        f_hum = hour_entry["humidity"]
                        f_baro = int(float(hour_entry["pressure"]) * 0.75006)
                        f_uv = hour_entry["uvIndex"]
                        
                        # Мониторинг предупреждений об осадках (только для сегодняшнего дня)
                        if day_idx == 0 and upcoming_precipitation == "NONE":
                            f_code = int(hour_entry["weatherCode"])
                            if f_code >= 200:
                                if f_code >= 386 and f_code <= 395:
                                    upcoming_precipitation = "STORM EXPECTED"
                                elif (f_code >= 323 and f_code <= 338) or (f_code >= 368 and f_code <= 371):
                                    upcoming_precipitation = "SNOW EXPECTED"
                                else:
                                    upcoming_precipitation = "RAIN EXPECTED"
                        
                        # Компактный пакет данных TEMP|WIND|HUMIDITY|BAROMETER|UV
                        pack_str = f"{f_temp}|{f_wind}|{f_hum}|{f_baro}|{f_uv}"
                        forecast_entries.append(f"F{day_idx}_{h_time:02d}:00={pack_str}")
                    
                    # 3. Автоматическое замыкание суток на 24:00 для каждого из 3 дней
                    forecast_entries.append(f"F{day_idx}_24:00={pack_str}")

        # 4. Формирование финальной структуры кэша
        output_data = [
            f"TEMP: {temp}°C (FEELS: {feels}°C)",
            f"WIND: {wind_ms} m/s ({wind_dir})",
            f"HUMIDITY: {humidity}%",
            f"BAROMETER: {press_mm} mmHg",
            f"UV INDEX: {uv}",
            f"CODE: {w_code}",
            f"PREDICT: {upcoming_precipitation}"
        ]

        for h_entry in history[:-1]:
            h_pack = f"{h_entry['temp']}|{h_entry['wind']}|{h_entry['hum']}|{h_entry['baro']}|{h_entry['uv']}"
            output_data.append(f"H_{h_entry['time']}={h_pack}")
            
        for f_entry in forecast_entries:
            output_data.append(f_entry)

        with open(WEATHER_TXT, "w") as f:
            f.write("\n".join(output_data))

        print("SovIntel 3-Day Telemetry Matrix compiled successfully.")
except Exception as e:
    print(f"Error: {e}")
