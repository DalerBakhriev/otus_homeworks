.PHONY: prod_up
prod_up:
	docker-compose up -d --build && docker logs -f hasker_service

.PHONY: prod_down
prod_down:
	docker-compose down

.PHONY: dev
dev:
	python manage.py runserver
