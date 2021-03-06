from io import BytesIO
from threading import Lock

import matplotlib.pyplot as plt

from apps.bot.APIs.Covid19API import Covid19API
from apps.bot.APIs.amazon.AmazonTranslateAPI import AmazonTranslateAPI
from apps.bot.classes.Consts import Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import has_cyrillic

lock = Lock()


class Coronavirus(CommonCommand):
    name = "коронавирус"
    names = ["корона", "ковид"]
    help_text = "статистика по коронавирусу в разных странах"
    help_texts = [
        "- статистика в мире",
        "[название страны [график/гистограмма]] - статистика в этой стране"
    ]

    def start(self):
        self.bot.set_activity(self.event.peer_id)

        detail = False
        if self.event.args:
            country = self.event.args[0]
            if len(self.event.args) >= 2:
                _type = self.event.args[1].lower()
                if _type == "график" or _type.endswith('фик'):
                    detail = 'Graphic'
                # ))
                if _type in ["гист", "гистограмма"] or _type.endswith('ста') or _type.endswith('са'):
                    detail = 'Gist'
        else:
            country = "Мир"

        if country != "Мир":
            if has_cyrillic(country):
                amazon_translate_api = AmazonTranslateAPI()
                country_transliterate = amazon_translate_api.get_translate(country, 'en').replace(' ', '-')
            else:
                country_transliterate = country
        else:
            country_transliterate = None

        if country.lower() in ["сша", "usa"]:
            country_transliterate = "united-states"
        covid19_api = Covid19API(country_transliterate)
        result = covid19_api.get_by_country()
        if not result:
            raise PWarning("Не нашёл такой страны")
        msg = f"{country.capitalize()}\n\n{result}"
        if detail in ["Gist", "Graphic"]:
            self.platforms = [Platform.VK, Platform.TG]
            self.check_platforms()
            if detail == "Gist":
                datas = covid19_api.get_detail_by_country()
                _, a = plt.subplots()
                x = datas['Dates']
                y1 = datas['Active']
                y2 = datas['Deaths']
                y3 = datas['Recovered']
                y2_bottom = y1
                y3_bottom = [x + y for x, y in zip(y1, y2)]
                a.bar(x, y1, label="Болеют", color="#46aada", width=1)
                a.bar(x, y2, bottom=y2_bottom, label="Умершие", color="red", width=1)
                a.bar(x, y3, bottom=y3_bottom, label="Выздоровевшие", color="green", width=1)
                a.xaxis.set_visible(False)
            elif detail == "Graphic":
                datas = covid19_api.get_detail_by_country()
                plt.plot(datas['Recovered'], "bo-", label="Выздоровевшие", color="green")
                plt.plot(datas['Active'], "bo-", label="Больные", color="#46aada")
                plt.plot(datas['Deaths'], "bo-", label="Умершие", color="red")

            plt.title(country.capitalize())
            plt.xlabel('День')
            plt.ylabel('Количество людей')
            plt.legend()
            with lock:
                graphic = BytesIO()
                plt.savefig(graphic)
                plt.cla()

                attachments = self.bot.upload_photos(graphic)
                return {'msg': msg, 'attachments': attachments}
        else:
            return msg
