docker run --name redis-celery -p 6379:6379 -d redis
poetry.exe run celery -A app.celery worker --loglevel=info
poetry.exe run celery -A app.celery flower --port=5555
poetry run celery -A app.celery beat


poetry.exe run flask run --debugger --reload