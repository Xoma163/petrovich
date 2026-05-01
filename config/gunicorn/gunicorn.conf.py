import os

import environ


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env = environ.Env()
env.read_env(os.path.join(BASE_DIR, ".env"))

# Слушаем TCP-адрес и порт для nginx, Telegram webhook и локальных healthcheck-запросов.
bind_address = env.str("GUNICORN_BIND_ADDRESS", default="127.0.0.1")
bind_port = env.int("GUNICORN_BIND_PORT", default=10010)
bind = f"{bind_address}:{bind_port}"

# Количество worker-процессов для обработки запросов.
workers = 4

# Количество потоков внутри каждого worker.
threads = 2

# Временная директория в памяти, чтобы снизить I/O на диске.
worker_tmp_dir = "/dev/shm"

# Максимальное время обработки запроса.
timeout = 120

# Сколько даём worker на корректное завершение.
graceful_timeout = 30

# PID-файл процесса gunicorn.
pidfile = "config/petrovich.pid"

# Корень проекта.
chdir = "."

# WSGI entrypoint Django-приложения.
wsgi_app = "petrovich.wsgi:application"

# Логи доступа пишем в stdout.
accesslog = "-"

# Ошибки пишем в stderr/stdout потоки процесса.
errorlog = "-"

# Захватываем stdout/stderr приложения в gunicorn-логи.
capture_output = True
