#!/bin/bash
# ====================================================================
# SOVINTEL OS AUTOMATED DEPLOYMENT UNIT & SYSTEM INITIALIZER (v1.0)
# ====================================================================
set -e

echo "=== STARTING SOVINTEL OS DEPLOYMENT ==="

# 1. Обновление репозиториев и установка системных пакетов
echo "[1/5] Installing core system packages (VLC, Python, Git)..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-pygame vlc git curl

# 2. Установка компонентов для работы Bluetooth-пульта
echo "[2/5] Installing Python library components (evdev)..."
pip3 install evdev --break-system-packages || pip3 install evdev

# 3. Восстановление каноничной структуры директорий SovIntel
echo "[3/5] Rebuilding SovIntel directory tree..."
TARGET_DIR="/home/pi/pipi_terminal"
mkdir -p "$TARGET_DIR"
mkdir -p "$TARGET_DIR/screens"

# 4. Настройка Cron-расписания для внешних скриптов сбора метеоданных и новостей
echo "[4/5] Deploying Cron schedules for telemetry gatherers..."
(crontab -l 2>/dev/null | grep -v "weather.py" | grep -v "news_grabber.py" || true) > mycron
echo "*/30 * * * * python3 /home/pi/pipi_terminal/weather.py >/dev/null 2>&1" >> mycron
echo "0 * * * * python3 /home/pi/pipi_terminal/news_grabber.py >/dev/null 2>&1" >> mycron
crontab mycron
rm mycron

# 5. Создание системной службы автозапуска (Systemd Service) с задержкой 5 сек
echo "[5/5] Creating systemd service unit with 5s Bluetooth delay..."
sudo cat << 'SERVICE' | sudo tee /etc/systemd/system/pipiboy.service > /dev/null
[Unit]
Description=SovIntel PiPi-Boy Terminal Core Engine
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/pipi_terminal
ExecStartPre=/bin/sleep 5
ExecStart=/usr/bin/python3 /home/pi/pipi_terminal/terminal.py
Restart=always
RestartSec=3
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=pipiboy

[Install]
WantedBy=multi-user.target
SERVICE

# Перезапуск демона системных служб и активация автозапуска
sudo systemctl daemon-reload
sudo systemctl enable pipiboy.service

echo "=== SOVINTEL OS DEPLOYMENT SUCCESSFUL! SYSTEM REBOOT REQUIRED ==="
