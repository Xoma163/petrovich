from time import sleep

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from apps.bot.APIs.TimezoneDBAPI import TimezoneDBAPI
from apps.bot.APIs.YandexGeoAPI import YandexGeoAPI
from apps.bot.classes.consts.Consts import Role
from apps.bot.models import Users
from apps.service.models import City, TimeZone, Service


class Command(BaseCommand):

    @staticmethod
    def init_groups():
        groups = [{'name': x.name} for x in Role]
        for group in groups:
            if group['name'] == "админ конфы":
                continue
            Group.objects.update_or_create(name=group['name'], defaults=group)

    @staticmethod
    def init_users():
        anonymous_user = {
            'user_id': 'ANONYMOUS',
            'name': 'Аноним',
            'surname': 'Анонимов'
        }
        anon_user, _ = Users.objects.update_or_create(user_id=anonymous_user['user_id'], defaults=anonymous_user)
        group_user = Group.objects.get(name=Role.USER.name)
        anon_user.groups.add(group_user)
        anon_user.save()

        # api_anonymous_user = {
        #     'user': anon_user,
        #     'chat': None
        # }
        # APIUser.objects.update_or_create(user__id=api_anonymous_user['user'].id, defaults=api_anonymous_user)

    @staticmethod
    def init_cities_offline():
        cities = [
            {'name': 'Абакан', 'synonyms': 'абакан', 'timezone__name': 'Asia/Krasnoyarsk', 'lat': 53.721152,
             'lon': 91.442387},
            {'name': 'Альметьевск', 'synonyms': 'альметьевск', 'timezone__name': 'Europe/Moscow', 'lat': 54.901383,
             'lon': 52.297113},
            {'name': 'Ангарск', 'synonyms': 'ангарск', 'timezone__name': 'Asia/Irkutsk', 'lat': 52.544358,
             'lon': 103.88824},
            {'name': 'Арзамас', 'synonyms': 'арзамас', 'timezone__name': 'Europe/Moscow', 'lat': 55.386799,
             'lon': 43.814133},
            {'name': 'Армавир', 'synonyms': 'армавир', 'timezone__name': 'Asia/Yerevan', 'lat': 40.15541,
             'lon': 44.03873},
            {'name': 'Артём', 'synonyms': 'артём', 'timezone__name': 'Asia/Vladivostok', 'lat': 43.354804,
             'lon': 132.18563},
            {'name': 'Архангельск', 'synonyms': 'архангельск', 'timezone__name': 'Europe/Moscow', 'lat': 64.539911,
             'lon': 40.515753},
            {'name': 'Астрахань', 'synonyms': 'астрахань', 'timezone__name': 'Europe/Astrakhan', 'lat': 46.347869,
             'lon': 48.033574},
            {'name': 'Ачинск', 'synonyms': 'ачинск', 'timezone__name': 'Asia/Krasnoyarsk', 'lat': 56.269496,
             'lon': 90.495231},
            {'name': 'Балаково', 'synonyms': 'балаково', 'timezone__name': 'Europe/Saratov', 'lat': 52.018424,
             'lon': 47.819667},
            {'name': 'Балашиха', 'synonyms': 'балашиха', 'timezone__name': 'Europe/Moscow', 'lat': 55.796339,
             'lon': 37.938199},
            {'name': 'Барнаул', 'synonyms': 'барнаул', 'timezone__name': 'Asia/Barnaul', 'lat': 53.346785,
             'lon': 83.776856},
            {'name': 'Батайск', 'synonyms': 'батайск', 'timezone__name': 'Europe/Moscow', 'lat': 47.138333,
             'lon': 39.744469},
            {'name': 'Белгород', 'synonyms': 'белгород', 'timezone__name': 'Europe/Moscow', 'lat': 50.59566,
             'lon': 36.587223},
            {'name': 'Березники', 'synonyms': 'березники', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 59.407922,
             'lon': 56.804015},
            {'name': 'Бийск', 'synonyms': 'бийск', 'timezone__name': 'Asia/Barnaul', 'lat': 52.539297, 'lon': 85.21382},
            {'name': 'Благовещенск', 'synonyms': 'благовещенск', 'timezone__name': 'Asia/Yakutsk', 'lat': 50.29064,
             'lon': 127.527173},
            {'name': 'Брянск', 'synonyms': 'брянск', 'timezone__name': 'Europe/Moscow', 'lat': 53.243562,
             'lon': 34.363407},
            {'name': 'Великий Новгород', 'synonyms': 'великий новгород', 'timezone__name': 'Europe/Moscow',
             'lat': 58.52281, 'lon': 31.269915},
            {'name': 'Владивосток', 'synonyms': 'владивосток', 'timezone__name': 'Asia/Vladivostok', 'lat': 43.115536,
             'lon': 131.885485},
            {'name': 'Владикавказ', 'synonyms': 'владикавказ', 'timezone__name': 'Europe/Moscow', 'lat': 43.02115,
             'lon': 44.68196},
            {'name': 'Владимир', 'synonyms': 'владимир', 'timezone__name': 'Europe/Moscow', 'lat': 56.129057,
             'lon': 40.406635},
            {'name': 'Волгоград', 'synonyms': 'волгоград', 'timezone__name': 'Europe/Volgograd', 'lat': 48.707067,
             'lon': 44.516948},
            {'name': 'Волгодонск', 'synonyms': 'волгодонск', 'timezone__name': 'Europe/Moscow', 'lat': 47.519618,
             'lon': 42.20632},
            {'name': 'Волжский', 'synonyms': 'волжский', 'timezone__name': 'Europe/Volgograd', 'lat': 48.786293,
             'lon': 44.751867},
            {'name': 'Вологда', 'synonyms': 'вологда', 'timezone__name': 'Europe/Moscow', 'lat': 59.220496,
             'lon': 39.891523},
            {'name': 'Воронеж', 'synonyms': 'воронеж', 'timezone__name': 'Europe/Moscow', 'lat': 51.660781,
             'lon': 39.200269},
            {'name': 'Воткинск', 'synonyms': 'воткинск', 'timezone__name': 'Europe/Samara', 'lat': 57.051806,
             'lon': 53.987392},
            {'name': 'Грозный', 'synonyms': 'грозный', 'timezone__name': 'Europe/Moscow', 'lat': 43.31851,
             'lon': 45.694271},
            {'name': 'Дербент', 'synonyms': 'дербент', 'timezone__name': 'Europe/Moscow', 'lat': 42.057669,
             'lon': 48.288776},
            {'name': 'Дзержинск', 'synonyms': 'дзержинск', 'timezone__name': 'Europe/Moscow', 'lat': 56.238377,
             'lon': 43.461625},
            {'name': 'Димитровград', 'synonyms': 'димитровград', 'timezone__name': 'Europe/Ulyanovsk', 'lat': 54.217515,
             'lon': 49.623924},
            {'name': 'Евпатория', 'synonyms': 'евпатория', 'timezone__name': 'Europe/Simferopol', 'lat': 45.190629,
             'lon': 33.367634},
            {'name': 'Екатеринбург', 'synonyms': 'екатеринбург екб', 'timezone__name': 'Asia/Yekaterinburg',
             'lat': 56.838011, 'lon': 60.597465},
            {'name': 'Елец', 'synonyms': 'елец', 'timezone__name': 'Europe/Moscow', 'lat': 52.62419, 'lon': 38.503653},
            {'name': 'Ессентуки', 'synonyms': 'ессентуки', 'timezone__name': 'Europe/Moscow', 'lat': 44.044526,
             'lon': 42.85891},
            {'name': 'Жуковский', 'synonyms': 'жуковский', 'timezone__name': 'Europe/Moscow', 'lat': 55.597475,
             'lon': 38.119802},
            {'name': 'Златоуст', 'synonyms': 'златоуст', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 55.173108,
             'lon': 59.672425},
            {'name': 'Иваново', 'synonyms': 'иваново', 'timezone__name': 'Europe/Moscow', 'lat': 57.000348,
             'lon': 40.973921},
            {'name': 'Ижевск', 'synonyms': 'ижевск', 'timezone__name': 'Europe/Samara', 'lat': 56.852676,
             'lon': 53.206891},
            {'name': 'Иркутск', 'synonyms': 'иркутск', 'timezone__name': 'Asia/Irkutsk', 'lat': 52.287054,
             'lon': 104.281047},
            {'name': 'Йошкар-Ола', 'synonyms': 'йошкар-ола', 'timezone__name': 'Europe/Moscow', 'lat': 56.631595,
             'lon': 47.886178},
            {'name': 'Казань', 'synonyms': 'казань', 'timezone__name': 'Europe/Moscow', 'lat': 55.796289,
             'lon': 49.108795},
            {'name': 'Калининград', 'synonyms': 'калининград', 'timezone__name': 'Europe/Kaliningrad', 'lat': 54.710454,
             'lon': 20.512733},
            {'name': 'Калуга', 'synonyms': 'калуга', 'timezone__name': 'Europe/Moscow', 'lat': 54.513845,
             'lon': 36.261215},
            {'name': 'Каменск-Уральский', 'synonyms': 'каменск-уральский', 'timezone__name': 'Asia/Yekaterinburg',
             'lat': 56.414927, 'lon': 61.918708},
            {'name': 'Камышин', 'synonyms': 'камышин', 'timezone__name': 'Europe/Volgograd', 'lat': 50.083698,
             'lon': 45.407367},
            {'name': 'Каспийск', 'synonyms': 'каспийск', 'timezone__name': 'Europe/Moscow', 'lat': 42.890833,
             'lon': 47.635674},
            {'name': 'Кемерово', 'synonyms': 'кемерово', 'timezone__name': 'Asia/Novokuznetsk', 'lat': 55.354727,
             'lon': 86.088374},
            {'name': 'Керчь', 'synonyms': 'керчь', 'timezone__name': 'Europe/Simferopol', 'lat': 45.356219,
             'lon': 36.467378},
            {'name': 'Киров', 'synonyms': 'киров', 'timezone__name': 'Europe/Kirov', 'lat': 58.603591,
             'lon': 49.668014},
            {'name': 'Кисловодск', 'synonyms': 'кисловодск', 'timezone__name': 'Europe/Moscow', 'lat': 43.905225,
             'lon': 42.716796},
            {'name': 'Ковров', 'synonyms': 'ковров', 'timezone__name': 'Europe/Moscow', 'lat': 56.363628,
             'lon': 41.31122},
            {'name': 'Коломна', 'synonyms': 'коломна', 'timezone__name': 'Europe/Moscow', 'lat': 55.103152,
             'lon': 38.752917},
            {'name': 'Комсомольск-на-Амуре', 'synonyms': 'комсомольск-на-амуре', 'timezone__name': 'Asia/Vladivostok',
             'lat': 50.549923, 'lon': 137.007948},
            {'name': 'Копейск', 'synonyms': 'копейск', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 55.115692,
             'lon': 61.611574},
            {'name': 'Королёв', 'synonyms': 'королёв', 'timezone__name': 'Europe/Moscow', 'lat': 55.922212,
             'lon': 37.854629},
            {'name': 'Кострома', 'synonyms': 'кострома', 'timezone__name': 'Europe/Moscow', 'lat': 57.767961,
             'lon': 40.926858},
            {'name': 'Красногорск', 'synonyms': 'красногорск', 'timezone__name': 'Europe/Moscow', 'lat': 55.831099,
             'lon': 37.330192},
            {'name': 'Краснодар', 'synonyms': 'краснодар', 'timezone__name': 'Europe/Moscow', 'lat': 45.03547,
             'lon': 38.975313},
            {'name': 'Красноярск', 'synonyms': 'красноярск', 'timezone__name': 'Asia/Krasnoyarsk', 'lat': 56.010563,
             'lon': 92.852572},
            {'name': 'Купчино', 'synonyms': 'купчино', 'timezone__name': 'Europe/Moscow', 'lat': 59.87238,
             'lon': 30.370291},
            {'name': 'Курган', 'synonyms': 'курган', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 55.441004,
             'lon': 65.341118},
            {'name': 'Курск', 'synonyms': 'курск', 'timezone__name': 'Europe/Moscow', 'lat': 51.73083,
             'lon': 36.193186},
            {'name': 'Кызыл', 'synonyms': 'кызыл', 'timezone__name': 'Asia/Krasnoyarsk', 'lat': 51.719086,
             'lon': 94.437757},
            {'name': 'Ленинск-Кузнецкий', 'synonyms': 'ленинск-кузнецкий', 'timezone__name': 'Asia/Novokuznetsk',
             'lat': 54.663609, 'lon': 86.162243},
            {'name': 'Липецк', 'synonyms': 'липецк', 'timezone__name': 'Europe/Moscow', 'lat': 52.60882,
             'lon': 39.59922},
            {'name': 'Люберцы', 'synonyms': 'люберцы', 'timezone__name': 'Europe/Moscow', 'lat': 55.676494,
             'lon': 37.898116},
            {'name': 'Магнитогорск', 'synonyms': 'магнитогорск', 'timezone__name': 'Asia/Yekaterinburg',
             'lat': 53.407158, 'lon': 58.980282},
            {'name': 'Майкоп', 'synonyms': 'майкоп', 'timezone__name': 'Europe/Moscow', 'lat': 44.608865,
             'lon': 40.098548},
            {'name': 'Махачкала', 'synonyms': 'махачкала', 'timezone__name': 'Europe/Moscow', 'lat': 42.98306,
             'lon': 47.504682},
            {'name': 'Междуреченск', 'synonyms': 'междуреченск', 'timezone__name': 'Asia/Novokuznetsk',
             'lat': 53.686596, 'lon': 88.070372},
            {'name': 'Миасс', 'synonyms': 'миасс', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 55.046414,
             'lon': 60.108081},
            {'name': 'Москва', 'synonyms': 'москва', 'timezone__name': 'Europe/Moscow', 'lat': 55.753215,
             'lon': 37.622504},
            {'name': 'Мурманск', 'synonyms': 'мурманск', 'timezone__name': 'Europe/Moscow', 'lat': 68.970682,
             'lon': 33.074981},
            {'name': 'Муром', 'synonyms': 'муром', 'timezone__name': 'Europe/Moscow', 'lat': 55.579169,
             'lon': 42.052411},
            {'name': 'Мытищи', 'synonyms': 'мытищи', 'timezone__name': 'Europe/Moscow', 'lat': 55.910483,
             'lon': 37.736402},
            {'name': 'Набережные Челны', 'synonyms': 'набережные челны', 'timezone__name': 'Europe/Moscow',
             'lat': 55.740776, 'lon': 52.406384},
            {'name': 'Находка', 'synonyms': 'находка', 'timezone__name': 'Asia/Vladivostok', 'lat': 42.824037,
             'lon': 132.892811},
            {'name': 'Невинномысск', 'synonyms': 'невинномысск', 'timezone__name': 'Europe/Moscow', 'lat': 44.638287,
             'lon': 41.936061},
            {'name': 'Нефтекамск', 'synonyms': 'нефтекамск', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 56.088408,
             'lon': 54.248236},
            {'name': 'Нефтеюганск', 'synonyms': 'нефтеюганск', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 61.088212,
             'lon': 72.616331},
            {'name': 'Нижневартовск', 'synonyms': 'нижневартовск', 'timezone__name': 'Asia/Yekaterinburg',
             'lat': 60.938545, 'lon': 76.558902},
            {'name': 'Нижнекамск', 'synonyms': 'нижнекамск', 'timezone__name': 'Europe/Moscow', 'lat': 55.63407,
             'lon': 51.809112},
            {'name': 'Нижний Новгород', 'synonyms': 'нижний новгород', 'timezone__name': 'Europe/Moscow',
             'lat': 56.326797, 'lon': 44.006516},
            {'name': 'Нижний Тагил', 'synonyms': 'нижний тагил', 'timezone__name': 'Asia/Yekaterinburg',
             'lat': 57.907605, 'lon': 59.972211},
            {'name': 'Новокузнецк', 'synonyms': 'новокузнецк', 'timezone__name': 'Asia/Novokuznetsk', 'lat': 53.757547,
             'lon': 87.136044},
            {'name': 'Новокуйбышевск', 'synonyms': 'новокуйбышевск', 'timezone__name': 'Europe/Samara',
             'lat': 53.099469, 'lon': 49.947767},
            {'name': 'Новомосковск', 'synonyms': 'новомосковск', 'timezone__name': 'Europe/Moscow', 'lat': 54.010993,
             'lon': 38.290896},
            {'name': 'Новороссийск', 'synonyms': 'новороссийск', 'timezone__name': 'Europe/Moscow', 'lat': 44.723912,
             'lon': 37.768974},
            {'name': 'Новосибирск', 'synonyms': 'новосибирск', 'timezone__name': 'Asia/Novosibirsk', 'lat': 55.030199,
             'lon': 82.92043},
            {'name': 'Новочебоксарск', 'synonyms': 'новочебоксарск', 'timezone__name': 'Europe/Moscow',
             'lat': 56.109551, 'lon': 47.479125},
            {'name': 'Новочеркасск', 'synonyms': 'новочеркасск', 'timezone__name': 'Europe/Moscow', 'lat': 47.422052,
             'lon': 40.093725},
            {'name': 'Новошахтинск', 'synonyms': 'новошахтинск', 'timezone__name': 'Europe/Moscow', 'lat': 47.754315,
             'lon': 39.934696},
            {'name': 'Новый Уренгой', 'synonyms': 'новый уренгой', 'timezone__name': 'Asia/Yekaterinburg',
             'lat': 66.083963, 'lon': 76.680974},
            {'name': 'Норильск', 'synonyms': 'норильск', 'timezone__name': 'Asia/Krasnoyarsk', 'lat': 69.343985,
             'lon': 88.210384},
            {'name': 'Ноябрьск', 'synonyms': 'ноябрьск', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 63.201801,
             'lon': 75.450938},
            {'name': 'Обнинск', 'synonyms': 'обнинск', 'timezone__name': 'Europe/Moscow', 'lat': 55.11201,
             'lon': 36.586531},
            {'name': 'Одинцово', 'synonyms': 'одинцово', 'timezone__name': 'Europe/Moscow', 'lat': 55.678859,
             'lon': 37.263986},
            {'name': 'Октябрьский', 'synonyms': 'октябрьский', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 54.481448,
             'lon': 53.46557},
            {'name': 'Оленегорск', 'synonyms': 'оленегорск', 'timezone__name': 'Europe/Moscow', 'lat': 68.140457,
             'lon': 33.270095},
            {'name': 'Омск', 'synonyms': 'омск', 'timezone__name': 'Asia/Omsk', 'lat': 54.989342, 'lon': 73.368212},
            {'name': 'Оренбург', 'synonyms': 'оренбург', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 51.768199,
             'lon': 55.096955},
            {'name': 'Орехово-Зуево', 'synonyms': 'орехово-зуево', 'timezone__name': 'Europe/Moscow', 'lat': 55.805837,
             'lon': 38.981592},
            {'name': 'Орёл', 'synonyms': 'орёл', 'timezone__name': 'Europe/Moscow', 'lat': 52.970371, 'lon': 36.063837},
            {'name': 'Орск', 'synonyms': 'орск', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 51.229362,
             'lon': 58.475196},
            {'name': 'Пенза', 'synonyms': 'пенза', 'timezone__name': 'Europe/Moscow', 'lat': 53.195042,
             'lon': 45.018316},
            {'name': 'Первоуральск', 'synonyms': 'первоуральск', 'timezone__name': 'Asia/Yekaterinburg',
             'lat': 56.905839, 'lon': 59.943249},
            {'name': 'Пермь', 'synonyms': 'пермь', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 58.01045,
             'lon': 56.229434},
            {'name': 'Петрозаводск', 'synonyms': 'петрозаводск', 'timezone__name': 'Europe/Moscow', 'lat': 61.785017,
             'lon': 34.346878}, {'name': 'Петропавловск-Камчатский', 'synonyms': 'петропавловск-камчатский',
                                 'timezone__name': 'Asia/Kamchatka', 'lat': 53.024075, 'lon': 158.643566},
            {'name': 'Подольск', 'synonyms': 'подольск', 'timezone__name': 'Europe/Moscow', 'lat': 55.431177,
             'lon': 37.544737},
            {'name': 'Прибой', 'synonyms': 'прибой', 'timezone__name': 'Europe/Samara', 'lat': 52.8689435,
             'lon': 49.6516931},
            {'name': 'Прокопьевск', 'synonyms': 'прокопьевск', 'timezone__name': 'Asia/Novokuznetsk', 'lat': 53.884487,
             'lon': 86.750055},
            {'name': 'Псков', 'synonyms': 'псков', 'timezone__name': 'Europe/Moscow', 'lat': 57.819274,
             'lon': 28.332451},
            {'name': 'Пушкино', 'synonyms': 'пушкино', 'timezone__name': 'Europe/Moscow', 'lat': 56.011182,
             'lon': 37.847047},
            {'name': 'Пятигорск', 'synonyms': 'пятигорск', 'timezone__name': 'Europe/Moscow', 'lat': 44.039795,
             'lon': 43.070634},
            {'name': 'Ростов-на-Дону', 'synonyms': 'ростов-на-дону', 'timezone__name': 'Europe/Moscow',
             'lat': 47.222078, 'lon': 39.720349},
            {'name': 'Рубцовск', 'synonyms': 'рубцовск', 'timezone__name': 'Asia/Barnaul', 'lat': 51.501207,
             'lon': 81.2078},
            {'name': 'Рыбинск', 'synonyms': 'рыбинск', 'timezone__name': 'Europe/Moscow', 'lat': 58.048454,
             'lon': 38.858406},
            {'name': 'Рязань', 'synonyms': 'рязань', 'timezone__name': 'Europe/Moscow', 'lat': 54.629216,
             'lon': 39.736375},
            {'name': 'Салават', 'synonyms': 'салават', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 53.361651,
             'lon': 55.924672},
            {'name': 'Самара', 'synonyms': 'самара смр', 'timezone__name': 'Europe/Samara', 'lat': 53.195538,
             'lon': 50.101783},
            {'name': 'Санкт-Петербург', 'synonyms': 'санкт-петербург спб питер петербург',
             'timezone__name': 'Europe/Moscow',
             'lat': 59.938951, 'lon': 30.315635},
            {'name': 'Саранск', 'synonyms': 'саранск', 'timezone__name': 'Europe/Moscow', 'lat': 54.187433,
             'lon': 45.183938},
            {'name': 'Сарапул', 'synonyms': 'сарапул', 'timezone__name': 'Europe/Samara', 'lat': 56.461621,
             'lon': 53.803678},
            {'name': 'Саратов', 'synonyms': 'саратов', 'timezone__name': 'Europe/Saratov', 'lat': 51.533103,
             'lon': 46.034158},
            {'name': 'Севастополь', 'synonyms': 'севастополь', 'timezone__name': 'Europe/Simferopol', 'lat': 44.556972,
             'lon': 33.526402},
            {'name': 'Северодвинск', 'synonyms': 'северодвинск', 'timezone__name': 'Europe/Moscow', 'lat': 64.562501,
             'lon': 39.818175},
            {'name': 'Северск', 'synonyms': 'северск', 'timezone__name': 'Asia/Tomsk', 'lat': 56.603185,
             'lon': 84.880913},
            {'name': 'Сергиев Посад', 'synonyms': 'сергиев посад', 'timezone__name': 'Europe/Moscow', 'lat': 56.315311,
             'lon': 38.135963},
            {'name': 'Серпухов', 'synonyms': 'серпухов', 'timezone__name': 'Europe/Moscow', 'lat': 54.913676,
             'lon': 37.416601},
            {'name': 'Симферополь', 'synonyms': 'симферополь', 'timezone__name': 'Europe/Simferopol', 'lat': 44.948237,
             'lon': 34.100318},
            {'name': 'Смоленск', 'synonyms': 'смоленск', 'timezone__name': 'Europe/Moscow', 'lat': 54.782635,
             'lon': 32.045251},
            {'name': 'Сочи', 'synonyms': 'сочи', 'timezone__name': 'Europe/Moscow', 'lat': 43.585525, 'lon': 39.723062},
            {'name': 'Ставрополь', 'synonyms': 'ставрополь', 'timezone__name': 'Europe/Moscow', 'lat': 45.04333,
             'lon': 41.969101},
            {'name': 'Старый Оскол', 'synonyms': 'старый оскол', 'timezone__name': 'Europe/Moscow', 'lat': 51.298075,
             'lon': 37.833447},
            {'name': 'Стерлитамак', 'synonyms': 'стерлитамак', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 53.630403,
             'lon': 55.930825},
            {'name': 'Сургут', 'synonyms': 'сургут', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 61.254035,
             'lon': 73.396221},
            {'name': 'Сызрань', 'synonyms': 'сызрань', 'timezone__name': 'Europe/Samara', 'lat': 53.155782,
             'lon': 48.474485},
            {'name': 'Сыктывкар', 'synonyms': 'сыктывкар', 'timezone__name': 'Europe/Moscow', 'lat': 61.668793,
             'lon': 50.836399},
            {'name': 'Таганрог', 'synonyms': 'таганрог', 'timezone__name': 'Europe/Moscow', 'lat': 47.22064,
             'lon': 38.914713},
            {'name': 'Тамбов', 'synonyms': 'тамбов', 'timezone__name': 'Europe/Moscow', 'lat': 52.721219,
             'lon': 41.452274},
            {'name': 'Тверь', 'synonyms': 'тверь', 'timezone__name': 'Europe/Moscow', 'lat': 56.859847,
             'lon': 35.911995},
            {'name': 'Тольятти', 'synonyms': 'тольятти тлт', 'timezone__name': 'Europe/Samara', 'lat': 53.5088,
             'lon': 49.41918},
            {'name': 'Томск', 'synonyms': 'томск', 'timezone__name': 'Asia/Tomsk', 'lat': 56.48464, 'lon': 84.947649},
            {'name': 'Тула', 'synonyms': 'тула', 'timezone__name': 'Europe/Moscow', 'lat': 54.193122, 'lon': 37.617348},
            {'name': 'Тюмень', 'synonyms': 'тюмень', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 57.153033,
             'lon': 65.534328},
            {'name': 'Улан-Удэ', 'synonyms': 'улан-удэ', 'timezone__name': 'Asia/Irkutsk', 'lat': 51.834464,
             'lon': 107.584574},
            {'name': 'Ульяновск', 'synonyms': 'ульяновск', 'timezone__name': 'Europe/Ulyanovsk', 'lat': 54.314192,
             'lon': 48.403123},
            {'name': 'Уссурийск', 'synonyms': 'уссурийск', 'timezone__name': 'Asia/Vladivostok', 'lat': 43.797273,
             'lon': 131.95178},
            {'name': 'Уфа', 'synonyms': 'уфа', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 54.735147,
             'lon': 55.958727},
            {'name': 'Хабаровск', 'synonyms': 'хабаровск', 'timezone__name': 'Asia/Vladivostok', 'lat': 48.480223,
             'lon': 135.071917},
            {'name': 'Хасавюрт', 'synonyms': 'хасавюрт', 'timezone__name': 'Europe/Moscow', 'lat': 43.246265,
             'lon': 46.590044},
            {'name': 'Химки', 'synonyms': 'химки', 'timezone__name': 'Europe/Moscow', 'lat': 55.88874, 'lon': 37.43039},
            {'name': 'Чебоксары', 'synonyms': 'чебоксары', 'timezone__name': 'Europe/Moscow', 'lat': 56.146277,
             'lon': 47.251079},
            {'name': 'Челябинск', 'synonyms': 'челябинск', 'timezone__name': 'Asia/Yekaterinburg', 'lat': 55.159897,
             'lon': 61.402554},
            {'name': 'Череповец', 'synonyms': 'череповец', 'timezone__name': 'Europe/Moscow', 'lat': 59.122612,
             'lon': 37.903461},
            {'name': 'Черкесск', 'synonyms': 'черкесск', 'timezone__name': 'Europe/Moscow', 'lat': 44.228374,
             'lon': 42.04827},
            {'name': 'Чита', 'synonyms': 'чита', 'timezone__name': 'Asia/Chita', 'lat': 52.033635, 'lon': 113.501049},
            {'name': 'Шахты', 'synonyms': 'шахты', 'timezone__name': 'Europe/Moscow', 'lat': 47.709601,
             'lon': 40.215797},
            {'name': 'Щёлково', 'synonyms': 'щёлково', 'timezone__name': 'Europe/Moscow', 'lat': 55.920875,
             'lon': 37.991622},
            {'name': 'Электросталь', 'synonyms': 'электросталь', 'timezone__name': 'Europe/Moscow', 'lat': 55.784445,
             'lon': 38.444849},
            {'name': 'Элиста', 'synonyms': 'элиста', 'timezone__name': 'Europe/Moscow', 'lat': 46.307743,
             'lon': 44.269759},
            {'name': 'Энгельс', 'synonyms': 'энгельс', 'timezone__name': 'Europe/Saratov', 'lat': 51.485489,
             'lon': 46.126783},
            {'name': 'Южно-Сахалинск', 'synonyms': 'южно-сахалинск', 'timezone__name': 'Asia/Sakhalin',
             'lat': 46.959179, 'lon': 142.738023},
            {'name': 'Якутск', 'synonyms': 'якутск', 'timezone__name': 'Asia/Yakutsk', 'lat': 62.027216,
             'lon': 129.732178},
            {'name': 'Ярославль', 'synonyms': 'ярославль', 'timezone__name': 'Europe/Moscow', 'lat': 57.626559,
             'lon': 39.893804}]

        for city in cities:
            timezone_obj, _ = TimeZone.objects.get_or_create(name=city['timezone__name'])
            city['timezone'] = timezone_obj
            del city['timezone__name']
            City.objects.update_or_create(name=city['name'], defaults=city)

    @staticmethod
    def init_cities_online():
        timezonedb_api = TimezoneDBAPI()
        yandexgeo_api = YandexGeoAPI()

        cities_list = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Нижний Новгород", "Казань",
                       "Самара", "Омск", "Челябинск", "Ростов-на-Дону", "Уфа", "Волгоград", "Пермь", "Красноярск",
                       "Воронеж", "Саратов", "Краснодар", "Тольятти", "Барнаул", "Ижевск", "Ульяновск", "Владивосток",
                       "Ярославль", "Иркутск", "Тюмень", "Махачкала", "Хабаровск", "Оренбург", "Новокузнецк",
                       "Кемерово", "Рязань", "Томск", "Астрахань", "Пенза", "Набережные Челны", "Липецк", "Тула",
                       "Киров", "Чебоксары", "Улан-Удэ", "Калининград", "Брянск", "Курск", "Иваново", "Магнитогорск",
                       "Тверь", "Ставрополь", "Севастополь", "Нижний Тагил", "Белгород", "Архангельск", "Владимир",
                       "Сочи", "Курган", "Симферополь", "Смоленск", "Калуга", "Чита", "Саранск", "Орёл", "Волжский",
                       "Череповец", "Владикавказ", "Мурманск", "Сургут", "Вологда", "Тамбов", "Стерлитамак", "Грозный",
                       "Якутск", "Кострома", "Комсомольск-на-Амуре", "Петрозаводск", "Таганрог", "Нижневартовск",
                       "Йошкар-ОлаБратск", "Новороссийск", "Дзержинск", "ШахтыНальчик", "Орск", "Сыктывкар",
                       "Нижнекамск", "Ангарск", "Старый Оскол", "Великий Новгород", "Балашиха", "Благовещенск",
                       "Прокопьевск", "Химки", "Псков", "Бийск", "Энгельс", "Рыбинск", "Балаково", "Северодвинск",
                       "Армавир", "Подольск", "Королёв", "Южно-Сахалинск", "Петропавловск-Камчатский", "Сызрань",
                       "Норильск", "Златоуст", "Каменск-Уральский", "Мытищи", "Люберцы", "Волгодонск", "Новочеркасск",
                       "Абакан", "Находка", "Уссурийск", "Березники", "Салават", "Электросталь", "Миасс",
                       "Первоуральск", "Керчь", "Рубцовск", "Альметьевск", "Ковров", "Коломна", "Майкоп", "Пятигорск",
                       "Одинцово", "Копейск", "Хасавюрт", "Новомосковск", "Кисловодск", "Серпухов", "Новочебоксарск",
                       "Нефтеюганск", "Димитровград", "Нефтекамск", "Черкесск", "Орехово-Зуево", "Дербент", "Камышин",
                       "Невинномысск", "Красногорск", "Муром", "Батайск", "Новошахтинск", "Сергиев Посад", "Ноябрьск",
                       "Щёлково", "Кызыл", "Октябрьский", "Ачинск", "Северск", "Новокуйбышевск", "Елец", "Арзамас",
                       "Евпатория", "Обнинск", "Новый Уренгой", "Каспийск", "Элиста", "Пушкино", "Жуковский", "Артём",
                       "Междуреченск", "Ленинск-Кузнецкий", "Сарапул", "Ессентуки", "Воткинск"]
        for city_name in cities_list:
            city_info = yandexgeo_api.get_city_info_by_name(city_name)
            if not city_info:
                print(f"Warn: не смог добавить город {city_name}. Ошибка получения координат")
                continue
            city_info['synonyms'] = city_info['name'].lower()
            # Увеличить задержку, если крашится получение таймзон
            sleep(0.5)
            timezone_name = timezonedb_api.get_timezone_by_coordinates(city_info['lat'], city_info['lon'])
            if not timezone_name:
                print(f"Warn: не смог добавить город {city_name}. Ошибка получения таймзоны")

            timezone_obj, _ = TimeZone.objects.get_or_create(name=timezone_name)

            city_info['timezone'] = timezone_obj
            City.objects.update_or_create(name=city_info['name'], defaults=city_info)
            print(f'add/update {city_info["name"]}')

    @staticmethod
    def init_services_db():
        Service.objects.get_or_create(name='mrazi_chats_index_from', defaults={'value': 0})
        Service.objects.get_or_create(name='mrazi_chats_index_to', defaults={'value': 20})

    def handle(self, *args, **options):
        self.init_groups()
        print('done init groups')

        self.init_users()
        print('done init users')

        self.init_cities_offline()
        # self.init_cities_online()
        print('done init cities')

        self.init_services_db()
        # self.init_cities_online()
        print('done init services_db')

        print("done all")
