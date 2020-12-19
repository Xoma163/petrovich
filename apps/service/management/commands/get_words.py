import time
from copy import copy

import gspread
from django.core.management.base import BaseCommand
from oauth2client.service_account import ServiceAccountCredentials

from apps.bot.classes.Exceptions import PWarning
from apps.service.models import Words
from petrovich.settings import BASE_DIR


def dict_is_empty(_dict):
    new_dict = copy(_dict)
    banned_ops = ['', ' ', 'None', None]
    new_dict.pop('id')
    new_dict.pop('type')
    flag = True
    for item in new_dict:
        flag = flag and (new_dict[item] in banned_ops)
        if not flag:
            return flag

    return flag


class Command(BaseCommand):

    def __init__(self):
        super().__init__()

    def handle(self, *args, **kwargs):
        scopes = ['https://spreadsheets.google.com/feeds',
                  'https://www.googleapis.com/auth/drive']

        creds = ServiceAccountCredentials.from_json_keyfile_name(f"{BASE_DIR}/secrets/Petrovich-google.json", scopes)
        client = gspread.authorize(creds)
        worksheets = client.open('Петрович').worksheets()

        time1 = time.time()
        created_words = 0
        msg = ""
        Words.objects.all().delete()
        try:
            for i, worksheet in enumerate(worksheets):
                if i == 0:
                    word_type = 'bad'
                else:
                    word_type = 'good'

                records = worksheet.get_all_records()
                for record in records:
                    record['type'] = word_type
                    if 'id' in record:
                        del record['id']

                    for item in record:
                        if not record[item] or record[item] == '' or str(record[item]).lower() == 'none':
                            record[item] = None
                    word = Words(**record)
                    word.save()
                    created_words += 1
            time2 = time.time()

            msg += f"\n" \
                   f"Время выполнения - {round(time2 - time1, 2)}\n" \
                   f"Добавлено слов - {created_words}"
            return msg
        except Exception as e:
            raise PWarning("Ошибка при обновлении слов\n"
                                 f"{str(e)}")
