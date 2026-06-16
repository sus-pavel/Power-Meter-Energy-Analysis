# PowerMeter

[English](README.md) | [Русский](README.ru.md)

PowerMeter - локальная платформа для мониторинга и аналитики энергопотребления по Modbus TCP. Приложение находит счетчики в локальной сети, проверяет найденные кандидаты, переводит подтвержденные устройства в управляемые, опрашивает измерения, сохраняет данные в SQLite и показывает рабочие панели с историей, DRPI-оценкой потенциала demand response и SSA-разложением временных рядов.

Текущая цель проекта - **PowerMeter.app для macOS**: настольная оболочка Tauri, которая автоматически запускает локальный FastAPI backend и показывает React/Vite frontend. PowerMeter не является облачным SaaS-сервисом и не является полноценной SCADA-системой. Это локальный инструмент для мониторинга, лабораторной проверки, пилотных внедрений и аналитики энергетических данных.

Ключевые темы: energy-monitoring, modbus-tcp, fastapi, react, tauri, sqlite, demand-response, time-series, ssa, power-systems.

## Рабочий процесс

```text
Обнаружение Modbus TCP
  → проверка кандидатов
  → добавление устройств
  → управляемые устройства
  → опрос
  → измерения
  → агрегация
  → тренды
  → DRPI
  → SSA
  → dashboard
```

## Технологии

- Backend: FastAPI, Uvicorn, Pydantic, SQLite.
- Frontend: React, Vite, TypeScript.
- Desktop: Tauri v2 для macOS-пакетирования и управления процессом backend.
- Протокол устройств: Modbus TCP с более безопасными режимами сканирования Unit ID.
- Аналитика: DRPI для оценки потенциала demand response и SSA для разложения временных рядов.

## Возможности

- Локальная работа через `PowerMeter.app`.
- FastAPI backend запускается и завершается настольной оболочкой.
- SQLite база хранится в `~/Library/Application Support/PowerMeter/`.
- Обнаружение устройств Modbus TCP.
- Настраиваемые и более безопасные режимы сканирования Unit ID.
- Проверка кандидатов, fingerprinting и добавление устройств.
- Управляемый список устройств и управление опросом.
- Хранение измерений и агрегация в SQLite.
- Исторические графики.
- DRPI-аналитика потенциала demand response.
- SSA-анализ временных рядов.
- React dashboard и страницы аналитики.
- Скрипты диагностики и сброса локальных данных приложения.

## Текущие ограничения

- macOS beta-приложение не подписано и не notarized, поэтому Gatekeeper может показать предупреждение.
- Это локальная beta-версия, а не промышленный дистрибутив.
- Карты регистров Modbus могут требовать ручной настройки под конкретную модель счетчика.
- PowerMeter не является SCADA/control-платформой и не отправляет управляющие команды.
- Нет облачной синхронизации и облачных аккаунтов.
- Пакеты для Windows и Linux пока не реализованы.
- Автообновление и полноценный подписанный installer - задачи будущих версий.

## Быстрый старт на macOS

Соберите приложение:

```bash
scripts/build_macos_app.sh
```

Готовый bundle появится здесь:

```text
src-tauri/target/release/bundle/macos/PowerMeter.app
```

Запустите приложение из Finder или командой:

```bash
open -n src-tauri/target/release/bundle/macos/PowerMeter.app
```

Упакованный backend слушает только:

```text
http://127.0.0.1:8765
```

Данные и логи приложения находятся в:

```text
~/Library/Application Support/PowerMeter/
```

Подробности: [docs/MACOS_INSTALL_AND_RUN.md](docs/MACOS_INSTALL_AND_RUN.md) и [docs/DESKTOP_TROUBLESHOOTING.md](docs/DESKTOP_TROUBLESHOOTING.md).

## Разработка

Backend в режиме разработки:

```bash
uvicorn backend.app.main:app --reload
```

Frontend в режиме разработки:

```bash
cd frontend
npm install
npm run dev
```

В обычном браузерном режиме frontend использует `http://127.0.0.1:8000`, если не задан `VITE_API_BASE_URL`. В desktop-режиме используется `http://127.0.0.1:8765`.

## Документация

- [Архитектура](docs/APP_ARCHITECTURE.md)
- [Руководство пользователя](docs/USER_GUIDE.md)
- [Руководство разработчика](docs/DEVELOPER_GUIDE.md)
- [Установка и запуск на macOS](docs/MACOS_INSTALL_AND_RUN.md)
- [Диагностика desktop-версии](docs/DESKTOP_TROUBLESHOOTING.md)
- [Обнаружение и подключение Modbus](docs/MODBUS_DISCOVERY_AND_ONBOARDING.md)
- [DRPI и SSA](docs/ANALYTICS_DRPI_SSA.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)
- [Security notes](docs/SECURITY_NOTES.md)

Исторические stage-документы перенесены в [docs/archive/stages](docs/archive/stages).

## Лицензия

См. [LICENSE](LICENSE).
