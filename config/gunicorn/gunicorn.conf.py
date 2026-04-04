# Слушаем unix socket, который затем проксирует nginx.
bind = "unix:config/petrovich.sock"

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
