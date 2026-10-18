DOCKER_COMPOSE = docker compose

.DEFAULT_GOAL := help

.PHONY: help env detect-node up down logs sub-log monitor recreate send send-at send-every set-position ping stop list

help: ## Показать список команд
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-15s %s\n", $$1, $$2}'

env: ## Создать .env и определить ноду
	@if [ -f .env ]; then echo ".env уже существует"; exit 1; fi
	@cp .env.example .env
	@bash scripts/detect-node.sh

detect-node: ## Определить ноду и обновить .env
	@bash scripts/detect-node.sh

up: ## Собрать и запустить
	@mkdir -p meshmonitor-data
	@mkdir -p subscriber-data
	${DOCKER_COMPOSE} up -d --build --remove-orphans

down: ## Остановить
	${DOCKER_COMPOSE} down --remove-orphans

logs: ## Логи прокси
	${DOCKER_COMPOSE} logs -f mqtt-proxy

sub-log: ## Входящие сообщения из MQTT
	${DOCKER_COMPOSE} logs -f subscriber

monitor: ## Мониторинг трафика в реальном времени
	@docker exec -it mqtt-sub python3 /monitor.py

recreate: ## Пересоздать контейнеры
	${DOCKER_COMPOSE} down --remove-orphans
	${DOCKER_COMPOSE} up -d --build --remove-orphans

send: ## Отправить сообщение сейчас
	@bash scripts/send.sh

send-at: ## Отправить один раз в указанное время
	@bash scripts/send-at.sh

send-every: ## Отправлять с интервалом
	@bash scripts/send-every.sh

set-position: ## Задать координаты: make set-position LAT=45.03 LON=38.97 ALT=30
	@docker exec mqtt-sender python3 /set-position.py $(LAT) $(LON) $(ALT)

ping: ## Отправить ping
	@docker exec -e MSG_TEXT="ping" mqtt-sender python3 /send.py

stop: ## Удалить задание по имени
	@bash scripts/stop.sh

list: ## Показать активные задания
	@bash scripts/list.sh