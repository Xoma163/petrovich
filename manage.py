#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def _delete_cache_activity_keys():
    """
    Удаление активити в кэше при запуске сервера
    """

    from django.core.cache import cache

    activity_keys = cache.keys("activity_*")  # noqa
    for key in activity_keys:
        cache.delete(key)


def one_time_script_on_run_server():
    """
    Метод запускается при старте сервера runserver
    """

    _delete_cache_activity_keys()


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petrovich.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Простите
    if sys.argv and sys.argv[1].lower() == "runserver":
        one_time_script_on_run_server()

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
