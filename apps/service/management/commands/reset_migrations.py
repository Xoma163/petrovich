import os
import re
import shutil
import tempfile

from django.core.management import BaseCommand
from django.core.management import call_command
from django.db import connection

class Command(BaseCommand):
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
            shutil.rmtree(os.path.join(app, 'migrations'))

    def handle(self, *args, **options):
        apps = options['apps']
        self.stdout.write("Reseting APP %s" % apps)
        for app in apps:
            self.delete_django_migrations_db_app(app)
            self.delete_migrations_files_app(app)
            self.stdout.write("APP (%s) deleted with success" % app)

        for app in apps:
            call_command('makemigrations', app)
            call_command('migrate', app, '--fake')
