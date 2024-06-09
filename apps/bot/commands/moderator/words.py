import time

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.service.models import Words as WordsModel
from petrovich.settings import BASE_DIR


class Words(Command):
    name = "слова"

    help_text = HelpText(
        commands_text="принудительно затягивает слова с Google Drive"
    )
    access = Role.MODERATOR
    mentioned = True

    def start(self) -> ResponseMessage:
        return self.get_words()

    @staticmethod
    def get_words():
        scopes = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_name(f"{BASE_DIR}/secrets/Petrovich-google.json", scopes)
        client = gspread.authorize(creds)
        worksheets = client.open('Петрович').worksheets()

        time1 = time.time()
        created_words = 0
        WordsModel.objects.all().delete()
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
                word = WordsModel(**record)
                word.save()
                created_words += 1
        time2 = time.time()

        answer = f"Время выполнения - {round(time2 - time1, 2)}\n" \
                 f"Добавлено слов - {created_words}"
        return ResponseMessage(ResponseMessageItem(text=answer))
