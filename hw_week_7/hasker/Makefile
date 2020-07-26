.PHONY: prod-up
prod-up:
	docker-compose up -d --build && docker logs -f hasker_service

.PHONY: prod-down
prod-down:
	docker-compose down

.PHONY: dev
dev:
	python manage.py runserver
