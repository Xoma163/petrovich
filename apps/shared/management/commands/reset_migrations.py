import os
from os.path import isfile, join

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


# ToDo: test
class Command(BaseCommand):
    """
    Пример запуска
    reset_migrations dev --apps games service shared commands gpt media_command meme notifies bot
    reset_migrations prod --apps games service shared commands gpt media_command meme notifies bot
    """

    help = 'Сброс миграций и "типа" squah их в одну миграцию'

    PROD = "prod"
    DEV = "dev"

    MODE = "mode"
    APPS = "apps"

    def __init__(self, *args, **kwargs):
        self.cursor = connection.cursor()
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        help_text = [
            "1) Запускаем скрипт на dev, он удалит все старые файлы миграций и сотрет их из django_migrations в БД",
            "2) Коммитим новые миграции, удаляем из гита старые (не забываем)",
            "3) Проверяем себя showmigrations",
            "4) Заливаем",
            "5) Запускаем скрипт на prod",
        ]
        parser.description = "\n".join(help_text)
        parser.add_argument(
            self.MODE,
            type=str,
            help='Стенд, на котором запускается скрипт. "prod" для продакшена, "dev" для дев стенда и локальной разработки.'
        )
        parser.add_argument(
            f"--{self.APPS}",
            type=str,
            nargs='+',
            help='Список приложений, в которых нужно произвести сброс миграций'
        )

    def delete_django_migrations_db_app(self, app: str):
        self.stdout.write(f'Сброс миграций приложения "{app}" в БД')
        self.cursor.execute(f"DELETE from django_migrations WHERE app = '{app}'")

    def delete_migrations_files_app(self, app: str):
        self.stdout.write(f'Удаление миграций приложения "{app}" в файлах')
        app_path = apps.get_app_config(app).path
        migrations_dir = os.path.join(app_path, 'migrations')
        if os.path.exists(migrations_dir):
            files = [f for f in os.listdir(migrations_dir) if isfile(join(migrations_dir, f))]
            files = list(filter(lambda x: x != '__init__.py', files))
            for file in files:
                os.remove(os.path.join(migrations_dir, file))
        self.stdout.write(f'Удаление миграций приложения "{app}" выполнено успешно в файлах')

    def handle(self, *args, **options):
        mode = options['mode']

        if mode not in [self.PROD, self.DEV]:
            raise CommandError(f'Некорректный "mode". Выберите "{self.PROD}" или "{self.DEV}"')

        is_dev_mode = mode == self.DEV

        apps = options['apps']
        apps_str = ", ".join(apps)
        self.stdout.write(f'Сброс миграций приложений "{apps_str}" в БД')
        for app in apps:
            self.delete_django_migrations_db_app(app)
            if is_dev_mode:
                self.delete_migrations_files_app(app)
                self.stdout.write(f'Миграции приложения "{app}" успешно удалены из БД')

        if is_dev_mode:
            for app in apps:
                call_command('makemigrations', app)

        for app in apps:
            call_command('migrate', app, '--fake')
