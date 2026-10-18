<div align="center">

# Meshtastic Local Node

**Локальный узел Meshtastic через USB. Работает 24/7 без приложения.**

![Platform](https://img.shields.io/badge/platform-Linux-blue)
![License](https://img.shields.io/badge/license-MIT-green)

</div>

---

Нода подключается к компьютеру через USB и работает постоянно. Телефон не требуется.

Что умеет:

- принимает сообщения из эфира
- взаимодействует по протоколу MQTT на приём и передачу данных
- отправляет сообщения по команде, при необходимости можно настроить расписание рассылки
- работает без приложения
- работает с одним каналом

Всё в Docker, работает на Linux. Подходит для стационарных нод.

[⬆ Наверх](#meshtastic-local-node)

## Содержание

- [Требования](#требования)
- [Определение USB-порта ноды](#определение-usb-порта-ноды)
- [Права на USB-порт](#права-на-usb-порт)
- [Установка](#установка)
- [Использование](#использование)
- [Команды](#команды)
- [Структура проекта](#структура-проекта)
- [Как это работает](#как-это-работает)
- [Ограничения](#ограничения)
- [Лицензия](#лицензия)

[⬆ Наверх](#meshtastic-local-node)

## Требования

- Linux (Debian/Ubuntu, Fedora или совместимый)
- Docker и Docker Compose v2
- USB-нода Meshtastic
- MQTT-брокер с логином и паролем
- `crontab` (для расписания)

[⬆ Наверх](#meshtastic-local-node)

## Определение USB-порта ноды

По умолчанию используется `/dev/ttyACM0`. Если у тебя другое устройство или несколько USB-устройств — порт будет другим.

### Как проверить

Подключи ноду по USB и выполни:

```bash
ls /dev/ttyACM* /dev/ttyUSB*
```

Возможные варианты:

| Устройство | Типичный порт |
| :--- | :--- |
| ESP32 (Heltec, T-Beam, T114 и др.) | `/dev/ttyACM0` |
| nRF52 через USB-адаптер | `/dev/ttyUSB0` |
| Несколько нод одновременно | `/dev/ttyACM0`, `/dev/ttyACM1`, ... |

### Как изменить порт в проекте

Порт задаётся в `.env`, переменная `SERIAL_PORT`. Значение подставляется в `docker-compose.yml` в сервис `serial-bridge`. Внутри контейнера путь всегда `/dev/ttyACM0` — это фиксированное имя внутри, снаружи подставляется реальный.

[⬆ Наверх](#meshtastic-local-node)

## Права на USB-порт

Чтобы контейнеры могли открывать порт, пользователь должен быть в группе `dialout`.

```bash
groups
```

Если в списке нет `dialout` — добавь:

```bash
sudo usermod -aG dialout $USER
```

После этого **перезайди в сессию** (закрой и открой SSH) или выполни:

```bash
newgrp dialout
```

[⬆ Наверх](#meshtastic-local-node)

## Установка

### 1. Клонировать проект

```bash
git clone https://github.com/dmitrym-web/meshtastic-local-node
cd meshtastic-local-node
```

### 2. Создать `.env`

```bash
make env
```

Команда создаст `.env` из `.env.example` и запустит автоопределение ноды: найдёт подключённые USB-устройства, для каждого проверит, что это Meshtastic-нода, и запишет в `.env` два параметра — `SERIAL_PORT` (порт) и `NODE_ID` (ID ноды).

Затем открой `.env` и заполни оставшиеся значения:

```bash
nano .env
```

| Переменная | Пример | Назначение |
| :--- | :--- | :--- |
| `MQTT_BROKER` | `meshtastic.meshradio.online` | Адрес брокера |
| `MQTT_PORT` | `1883` | Порт брокера |
| `MQTT_USERNAME` | `user` | Логин |
| `MQTT_PASSWORD` | `pass` | Пароль |
| `MQTT_ROOT_TOPIC` | `msh/nvrsk` | Корневой топик |
| `CHANNEL_INDEX` | `0` | Номер канала |
| `CHANNEL` | `LongFast` | Канал (только один) |
| `CHANNEL_KEY` | `AQ==` | PSK-ключ канала |
| `SERIAL_PORT` | `/dev/ttyACM0` | Порт ноды на хосте |
| `NODE_ID` | `!950f28d9` | ID ноды |
| `SERIAL_BRIDGE_PORT` | `4403` | Порт serial-bridge |
| `MESHMONITOR_PORT` | `8181` | Порт веб-панели MeshMonitor |
| `MESHMONITOR_VIRTUAL_NODE_PORT` | `4404` | Порт Virtual Node |

### 3. Запустить

```bash
make up
```

При первом запуске контейнер `meshmonitor-init` автоматически подождет запуск MeshMonitor, создаст API-токен и включит Virtual Node. Тебе не нужно заходить в веб-интерфейс.

### 4. Проверить

```bash
docker ps
```

Должны быть запущены контейнеры: `serial-bridge`, `meshmonitor`, `mqtt-proxy`, `mqtt-sub`, `mqtt-sender`.

[⬆ Наверх](#meshtastic-local-node)

## Использование

### Отправить сообщение сейчас

```bash
make send
```

Спросит текст, отправит.

### Отправить один раз в указанное время

```bash
make send-at
```

Спросит время (`today 14:30` или `tomorrow 09:00`) и текст.

### Отправлять с интервалом

```bash
make send-every
```

Спросит имя задания, интервал (`30m`, `2h`, `1d`) и текст.

### Список активных заданий

```bash
make list
```

### Удалить задание

```bash
make stop
```

### Задать координаты ноды

```bash
make set-position LAT=55.7315633 LON=37.6564322 ALT=885
```

### Отправить ping

```bash
make ping
```

### Мониторинг трафика

```bash
make monitor
```

Показывает входящие и исходящие сообщения. Выход — `Ctrl+C`.

[⬆ Наверх](#meshtastic-local-node)

## Команды

| Команда | Действие |
| :--- | :--- |
| `make help` | Показать список команд |
| `make env` | Создать `.env` и определить ноду |
| `make detect-node` | Определить ноду и обновить `.env` |
| `make up` | Собрать и запустить |
| `make down` | Остановить |
| `make logs` | Логи прокси |
| `make sub-log` | Входящие сообщения из MQTT |
| `make monitor` | Мониторинг трафика в реальном времени |
| `make recreate` | Пересоздать контейнеры |
| `make send` | Отправить сообщение сейчас |
| `make send-at` | Отправить один раз в указанное время |
| `make send-every` | Отправлять с интервалом |
| `make set-position` | Задать координаты ноды |
| `make ping` | Отправить ping |
| `make list` | Показать активные задания |
| `make stop` | Удалить задание по имени |

[⬆ Наверх](#meshtastic-local-node)

## Структура проекта

```
.
├── docker-compose.yml
├── .env
├── .env.example
├── .gitignore
├── Makefile
├── README.md
├── TODO.md
├── meshmonitor-data/
├── meshmonitor-secrets/
├── subscriber-data/
├── scripts/
│   ├── send.sh
│   ├── send-at.sh
│   ├── send-every.sh
│   ├── send-scheduled-once.sh
│   ├── send-scheduled-repeat.sh
│   ├── detect-node.sh
│   ├── init-meshmonitor.sh
│   ├── stop.sh
│   └── list.sh
├── sender/
│   ├── Dockerfile
│   ├── send.py
│   └── set-position.py
└── subscriber/
    ├── Dockerfile
    ├── decode.py
    └── monitor.py
```

[⬆ Наверх](#meshtastic-local-node)

## Как это работает

### Компоненты

- `serial-bridge` — держит USB-порт ноды и отдаёт его по TCP.
- `meshmonitor` — подключается к `serial-bridge`, поднимает Virtual Node на порту 4404. Выступает единой точкой входа.
- `meshmonitor-init` — одноразовый контейнер, который автоматически настраивает Virtual Node через API при старте.
- `mqtt-proxy` — подключается к Virtual Node (`localhost:4404`), мостит ноду и MQTT-брокер.
- `sender` — подключается к Virtual Node (`localhost:4404`), отправляет текст в ноду.
- `subscriber` — слушает MQTT, расшифровывает и печатает входящие.

### Отправка сообщения

1. `sender/send.py` публикует лог-строку в MQTT для монитора.
2. Подключается к MeshMonitor по TCP.
3. Вызывает `sendText`. MeshMonitor передаёт пакет в ноду.
4. Нода отправляет пакет в эфир от своего ID.

### Приём сообщения из эфира

1. Нода принимает пакет из радио.
2. Отдаёт его MeshMonitor, а тот — `mqtt-proxy`.
3. `mqtt-proxy` публикует пакет в MQTT.
4. `subscriber` слушает топик, расшифровывает и печатает в лог.

[⬆ Наверх](#meshtastic-local-node)

## Ограничения

- **Только Linux.** На Windows не работает.
- **Один канал.** Для другого канала нужен отдельный экземпляр.
- **Нет локального веб-интерфейса.** Входящие сообщения видны в `make monitor`, `make sub-log`, в MeshMonitor и Telegram.

[⬆ Наверх](#meshtastic-local-node)

## Лицензия

MIT

[⬆ Наверх](#meshtastic-local-node)