import os.path
import pickle
import time
from copy import copy

from django.core.management.base import BaseCommand
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from apps.service.models import Words
from petrovich.settings import BASE_DIR, env


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

    # ToDo: не работает
    def handle(self, *args, **kwargs):
        PETROVICH_ID = env.str('GOOGLE_WORDS_PETROVICH_ID')
        RANGE_NAMES = env.str('GOOGLE_WORDS_RANGE_NAMES')
        API_KEY = env.str('GOOGLE_WORDS_API_KEY')
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

        creds = None
        if os.path.exists(BASE_DIR + '/secrets/google_token.pickle'):
            with open(BASE_DIR + '/secrets/google_token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(BASE_DIR + '/secrets/google_credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open(BASE_DIR + '/secrets/google_token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('sheets', 'v4', credentials=creds)
        result = service.spreadsheets().values().batchGet(spreadsheetId=PETROVICH_ID,
                                                          ranges=RANGE_NAMES,
                                                          key=API_KEY).execute()
        ranges = result.get('valueRanges', [])
        headers = []
        time1 = time.time()
        statistics = {'created': 0, 'updated': 0, 'deleted': 0, 'skipped': 0}

        try:
            for i, my_range in enumerate(ranges):
                if i == 0:
                    word_type = 'bad'
                    statistics['bad_words'] = len(my_range['values']) - 1
                else:
                    word_type = 'good'
                    statistics['good_words'] = len(my_range['values']) - 1

                for j, val in enumerate(my_range['values']):
                    if j != 0:
                        word_dict = {'type': word_type}
                        for k, item in enumerate(val):
                            if item != 'None' and item is not None and item != ' ' and item != '':
                                word_dict[headers[k]] = item
                            else:
                                word_dict[headers[k]] = None
                        if 'id' in word_dict:
                            if dict_is_empty(word_dict):
                                word_if_exist = Words.objects.filter(id=word_dict['id'])
                                if word_if_exist:
                                    word_if_exist.delete()
                                    statistics['deleted'] += 1
                                else:
                                    statistics['skipped'] += 1

                            else:
                                word = Words.objects.filter(id=word_dict['id'])
                                if len(word) > 0:
                                    existed_word_dict = word.first().__dict__
                                    existed_word_dict.pop('_state')
                                    existed_word_dict['id'] = str(existed_word_dict['id'])
                                    if word_dict == existed_word_dict:
                                        statistics['skipped'] += 1
                                    else:
                                        Words.objects.update_or_create(id=word_dict['id'], defaults=word_dict)
                                        statistics['updated'] += 1
                                else:
                                    Words(**word_dict).save()
                                    statistics['created'] += 1
                        else:
                            return f"Слово не имеет id. Проверьте - {word_dict}. Строка - {j}"

                    else:
                        headers = [header for header in val]

            msg = "Result: success\n" \
                  f"Time: {time.time() - time1}" \
                  f"\nStatistics:\n" \
                  f"created - {statistics['created']}\n" \
                  f"updated - {statistics['updated']}\n" \
                  f"deleted - {statistics['deleted']}\n" \
                  f"skipped - {statistics['skipped']}\n" \
                  f"total - {statistics['bad_words'] + statistics['good_words']}\n" \
                  f"-----\n" \
                  f"bad_words - {statistics['bad_words']}\n" \
                  f"good_words - {statistics['good_words']}\n"
            return msg
        except Exception as e:
            return "error " + str(e)
