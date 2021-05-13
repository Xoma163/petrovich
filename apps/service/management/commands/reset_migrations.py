import os
from os import listdir
from os.path import isfile, join

from django.core.management import BaseCommand
from django.core.management import call_command
from django.db import connection


class Command(BaseCommand):
    """
    Как пользоваться?
    1) На локале запускаем скрипт, он удалит все старые файлы миграций и сотрёт их из django_migrations в БД
    2) Коммитим новые миграции, удаляем из гита старые (не забываем)
    3) Проверяем себя showmigrations
    4) Заливаем и комментим строку с makemigrations
    5) Запускаем скрипт на проде

    Скрипт - сборная солянка из 3х других.
    """
    help = "Delete all migrations from one app, reset database and create one new migration"

    def __init__(self, *args, **kwargs):
        self.cursor = connection.cursor()
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('apps', nargs='+', type=str)

    def delete_django_migrations_db_app(self, app):
        self.stdout.write("Deleting APP (%s) in database" % app)
        self.cursor.execute("DELETE from django_migrations WHERE app = %s", [app])

    def delete_migrations_files_app(self, app):
        self.stdout.write("Deleting APP (%s) migrations files" % app)
        migrations_dir = os.path.join(app, 'migrations')
        if os.path.exists(migrations_dir):
            files = [f for f in listdir(migrations_dir) if isfile(join(migrations_dir, f))]
            files = list(filter(lambda x: x != '__init__.py', files))
            for file in files:
                os.remove(os.path.join(migrations_dir, file))

    def handle(self, *args, **options):
        apps = options['apps']
        self.stdout.write("Reseting APP %s" % apps)
        for app in apps:
            self.delete_django_migrations_db_app(app)
            # ToDo: uncomment on local. Comment on production
            self.delete_migrations_files_app(app)
            self.stdout.write("APP (%s) deleted with success" % app)

        # ToDo: uncomment on local. Comment on production
        for app in apps:
            call_command('makemigrations', app)

        for app in apps:
            call_command('migrate', app, '--fake')
