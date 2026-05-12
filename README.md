# SVD Online Energy Dashboard

Приложение для онлайн-сбора энергетических параметров с Modbus-счётчиков, записи данных в SQLite, агрегации временных рядов и расчёта показателей DRPI/SSA. В проекте есть сервисный пайплайн для сбора данных и FastAPI-веб-интерфейс для просмотра текущего состояния, истории, DRPI и SSA-аналитики.

## Возможности

- опрос Modbus TCP устройств по конфигурации YAML;
- запись сырых измерений в SQLite;
- агрегация данных по окнам 5, 10, 15, 30 и 60 минут;
- расчёт DRPI для отдельных счётчиков и суммарного потребления;
- SSA-анализ временных рядов;
- веб-интерфейс на FastAPI/Jinja2 с API-эндпоинтами для графиков.

## Структура проекта

```text
.
├── config/              # YAML-конфигурация сервисов
├── core/                # DRPI и SSA вычислительные модули
├── data/                # локальная SQLite БД, не публикуется в Git
├── services/            # collector, writer, aggregator, drpi service
├── web/                 # FastAPI-приложение, шаблоны и статические файлы
├── main.py              # запуск полного пайплайна
└── requirements.txt
```

## Быстрый старт

Требуется Python 3.11 или новее.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Создайте локальный конфиг устройств:

```bash
cp config/devices.example.yaml config/devices.yaml
```

Отредактируйте `config/devices.yaml`: укажите IP-адреса, Modbus unit id, регистры и включите нужные устройства.

## Запуск

Полный пайплайн сбора, записи, агрегации и DRPI:

```bash
python main.py
```

Веб-интерфейс:

```bash
uvicorn web.app:app --host 0.0.0.0 --port 8000
```

После запуска откройте `http://localhost:8000`.

## Конфигурация

- `config/devices.yaml` — локальный список Modbus-устройств. Файл игнорируется Git, чтобы не публиковать адреса и топологию оборудования.
- `config/writer.yaml` — параметры SQLite и записи сырых данных.
- `config/aggregator.yaml` — окна агрегации и политика хранения raw-данных.
- `config/drpi.yaml` — параметры расчёта DRPI.
- `config/ssa.yaml` — параметры SSA-анализа.

SQLite-файлы в `data/` являются runtime-данными и не входят в репозиторий.

## Основные страницы и API

- `/overview` — обзор текущих показателей;
- `/history` — исторические временные ряды;
- `/drpi` — DRPI-дашборд;
- `/ssa` — SSA-анализ;
- `/docs` — Swagger UI со всеми API-эндпоинтами.

## Подготовка к публикации

Перед первым коммитом проверьте:

```bash
git status --short
python -m compileall main.py services core web
```

В публичный репозиторий не должны попадать:

- `data/*.db`, `data/*.db-wal`, `data/*.db-shm`;
- `.DS_Store`;
- `.env`;
- локальный `config/devices.yaml`.

## Лицензия

Лицензия пока не указана. Перед публикацией выберите подходящую лицензию, если проект должен быть доступен для использования другими людьми.

