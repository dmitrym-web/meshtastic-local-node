DOCKER_COMPOSE = docker compose

.DEFAULT_GOAL := help

.PHONY: help requirement env up down logs sub-log monitor recreate send send-at send-every set-position ping stop list backup restore

help: ## Показать список команд
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-15s %s\n", $$1, $$2}'

requirement: ## Проверить зависимости системы
	@bash scripts/requirement.sh

env: ## Создать .env и определить ноду
	@bash -c ' \
		if ! bash scripts/requirement.sh; then \
			exit 0; \
		fi; \
		if [ -f .env ]; then \
			echo -n "Файл .env существует. Перезаписать? (y/n): "; \
			read ans < /dev/tty; \
			if [ "$$ans" != "y" ] && [ "$$ans" != "Y" ]; then \
				echo "Файл .env не перезаписан."; \
				exit 0; \
			fi; \
		fi; \
		echo "Поиск ноды..."; \
		NODE_INFO=$$(bash scripts/detect-node.sh); \
		if [ $$? -eq 0 ]; then \
			if [ -f .env ]; then mv .env .env.bak; fi; \
			cp .env.example .env; \
			sed -i "s/^PUID=.*/PUID=$$(id -u)/" .env; \
			sed -i "s/^PGID=.*/PGID=$$(id -g)/" .env; \
			PORT=$$(echo "$$NODE_INFO" | grep "SERIAL_PORT=" | cut -d= -f2); \
			NODE_ID=$$(echo "$$NODE_INFO" | grep "NODE_ID=" | cut -d= -f2); \
			sed -i "s|^SERIAL_PORT=.*|SERIAL_PORT=$$PORT|" .env; \
			sed -i "s|^NODE_ID=.*|NODE_ID=$$NODE_ID|" .env; \
			echo "Готово. Не забудьте заполнить MQTT_BROKER, MQTT_USERNAME и MQTT_PASSWORD в файле .env."; \
		else \
			echo "Настройки .env не изменены."; \
		fi'

up: ## Собрать и запустить
	@mkdir -p meshmonitor-data
	@mkdir -p subscriber-data
	@mkdir -p meshmonitor-secrets
	@mkdir -p jobs
	@mkdir -p backups
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

backup: ## Создать архивы (интерактивно)
	@bash scripts/backup.sh

restore: ## Восстановить из архива (интерактивно)
	@bash scripts/restore.sh