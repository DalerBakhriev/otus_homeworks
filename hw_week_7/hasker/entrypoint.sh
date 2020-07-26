python manage.py migrate &&
gunicorn hasker.wsgi -w 4 -b 0.0.0.0:8080