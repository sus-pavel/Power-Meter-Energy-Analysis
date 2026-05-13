# Raspberry Pi Deployment

Инструкция описывает запуск PowerMeter Energy Dashboard на Raspberry Pi. Все приватные значения заменены на шаблоны: `<rpi-ip>`, `<user>`, `<SSID>`, `<PASSWORD>`, `<local-project-path>`.

## 1. Синхронизация проекта

Если проект переносится с рабочего компьютера на Raspberry Pi через `rsync`, исключайте runtime-данные и временные файлы:

```bash
rsync -av --progress \
  --exclude 'data/' \
  --exclude '.DS_Store' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  <local-project-path>/ <user>@<rpi-ip>:/home/<user>/Project/
```

Пример целевой папки на Raspberry Pi:

```text
/home/<user>/Project
```

Альтернативный вариант — клонировать репозиторий напрямую на Raspberry Pi:

```bash
git clone <repository-url> /home/<user>/Project
```

Локальный файл `config/devices.yaml` и база `data/energy.db` не должны храниться в публичном Git-репозитории. `config/devices.yaml` создаётся на Raspberry Pi из примера и заполняется под конкретную сеть Modbus-устройств.

## 2. Подключение по SSH

В своей сети подключитесь к плате:

```bash
ssh <user>@<rpi-ip>
```

Если Raspberry Pi находится в другой Wi-Fi сети, подключите клавиатуру и монитор, войдите локально и настройте Wi-Fi:

```bash
sudo nmcli device wifi connect "<SSID>" password "<PASSWORD>"
```

Полезные команды для Wi-Fi:

```bash
sudo nmcli device wifi list
sudo nmcli device wifi connect "<SSID>" password "<PASSWORD>" hidden yes
sudo nmcli --ask device wifi connect "<SSID>"
nmcli connection show
```

Команда `--ask` удобна, если не нужно сохранять пароль Wi-Fi в истории shell.

## 3. Подготовка проекта

Перейдите в папку проекта:

```bash
cd /home/<user>/Project
```

Создайте локальную конфигурацию устройств:

```bash
cp config/devices.example.yaml config/devices.yaml
nano config/devices.yaml
```

Укажите реальные IP-адреса Modbus TCP-счётчиков, `unit_id`, регистры, типы данных и включите нужные устройства.

## 4. Установка Python

Проект требует Python 3.11 или новее. Если в Raspberry Pi OS уже доступен подходящий Python, можно использовать системный пакет:

```bash
python3 --version
python3 -m venv venv
```

Если нужен Python 3.12, его можно собрать из исходников:

```bash
sudo apt update
sudo apt install -y build-essential libssl-dev zlib1g-dev \
  libncurses5-dev libgdbm-dev libnss3-dev libreadline-dev \
  libffi-dev libsqlite3-dev wget libbz2-dev

wget https://www.python.org/ftp/python/3.12.3/Python-3.12.3.tgz
tar -xf Python-3.12.3.tgz
cd Python-3.12.3

./configure --enable-optimizations
make -j$(nproc)
sudo make altinstall
```

После установки вернитесь в папку проекта и создайте виртуальное окружение:

```bash
cd /home/<user>/Project
python3.12 -m venv venv
```

## 5. Виртуальное окружение и зависимости

Активируйте окружение:

```bash
source venv/bin/activate
```

Проверьте, что используются Python и pip из папки проекта:

```bash
which python
which pip
python --version
```

Установите зависимости:

```bash
pip install -r requirements.txt
```

## 6. Systemd-сервис для пайпа

Процесс запускает сбор данных, запись в SQLite, агрегацию и расчёт DRPI через `main.py`.

Создайте systemd unit:

```bash
sudo nano /etc/systemd/system/energy-platform.service
```

Вставьте конфигурацию, заменив `<user>` при необходимости:

```ini
[Unit]
Description=Energy Platform Pipeline
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=<user>
Group=<user>
WorkingDirectory=/home/<user>/Project

ExecStart=/home/<user>/Project/venv/bin/python /home/<user>/Project/main.py

Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal

Environment=PYTHONUNBUFFERED=1
UMask=0022

[Install]
WantedBy=multi-user.target
```

Примените конфигурацию systemd:

```bash
sudo systemctl daemon-reload
```

Включите автозапуск:

```bash
sudo systemctl enable energy-platform.service
```

Запустите сервис:

```bash
sudo systemctl start energy-platform.service
```

Проверьте состояние:

```bash
sudo systemctl status energy-platform.service
```

Смотрите live-логи:

```bash
journalctl -u energy-platform.service -f
```

Управление сервисом:

```bash
sudo systemctl stop energy-platform.service
sudo systemctl restart energy-platform.service
sudo systemctl disable energy-platform.service
```

## 7. Запуск веб-интерфейса

Для ручного запуска веб-приложения:

```bash
cd /home/<user>/Project
source venv/bin/activate
python -m uvicorn web.app:app --host 0.0.0.0 --port 8000
```

После запуска откройте в браузере:

```text
http://<rpi-ip>:8000/overview
http://<rpi-ip>:8000/drpi
http://<rpi-ip>:8000/ssa
http://<rpi-ip>:8000/docs
```

## 8. Полезные команды

```bash
pwd
ls -la
cd /home/<user>/Project
systemctl status energy-platform.service
journalctl -u energy-platform.service -n 100
journalctl -u energy-platform.service -f
```

Для перемещения папки:

```bash
mv <source-path> <target-path>
```

Удаление папок выполняйте только если точно понимаете последствия:

```bash
rm -rf <folder>
```

## 9. Типовой порядок запуска после перезагрузки

Если `energy-platform.service` включён через `systemctl enable`, pipeline стартует автоматически после загрузки Raspberry Pi.

Проверить:

```bash
sudo systemctl status energy-platform.service
```

Веб-интерфейс при ручном запуске нужно поднять отдельно:

```bash
cd /home/<user>/Project
source venv/bin/activate
python -m uvicorn web.app:app --host 0.0.0.0 --port 8000
```
