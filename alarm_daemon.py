import time
from datetime import datetime
import config_manager
import vlc_engine

# Автономная фоновая служба контроля времени SovIntel Alarm Daemon
# Работает независимо от графического интерфейса терминала

def main():
    print("SovIntel Alarm Daemon successfully initialized. Monitoring state...")
    while True:
        now = datetime.now()
        # Каждую минуту перечитываем актуальное состояние конфигурационного JSON
        cfg = config_manager.load_settings()
        
        if cfg.get("alarm_enabled", False):
            # Проверяем совпадение часов и минут
            if now.strftime("%H:%M") == cfg.get("alarm_time", "07:00"):
                # Срабатывание триггера на старте минуты
                if now.second < 2:
                    print(f"ALARM TRIGGER ACTIVATED AT {now.strftime('%H:%M:%S')}")
                    # Берем выбранную станцию из конфига
                    station_idx = cfg.get("alarm_station_idx", 1)
                    # Будим на уверенной громкости в 60%
                    vlc_engine.play_station(station_idx, 60)
                    
        # Засыпаем на 1 секунду, чтобы не грузить ядро процессора
        time.sleep(1)

if __name__ == "__main__":
    main()
