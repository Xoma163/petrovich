from apps.bot.APIs.TimezoneDBAPI import TimezoneDBAPI
from apps.bot.APIs.YandexGeoAPI import YandexGeoAPI
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.service.models import City as CityModel, TimeZone


class City(CommonCommand):
    def __init__(self):
        names = ["город"]
        help_text = "Город - добавляет город в базу или устанавливает город пользователю"
        detail_help_text = "Город (название) - устанавливает пользователю город\n" \
                           "Город добавить (название) - добавляет новый город в базу (часовой пояс и координаты устанавливаются автоматически)\n" \
                           "Город - присылает текущий город пользователя"
        super().__init__(names, help_text, detail_help_text)

    def start(self):

        if self.event.args:
            if self.event.args[0] == 'добавить':
                self.check_args(2)
                city_name = self.event.args[1:len(self.event.args)]
                city_name = " ".join(city_name)
                city = add_city_to_db(city_name)
                return f"Добавил новый город - {city.name}"
            else:
                city_name = self.event.args[0]
                city = CityModel.objects.filter(synonyms__icontains=city_name).first()
                if not city:
                    raise RuntimeWarning("Не нашёл такого города. /город добавить (название)")
                else:
                    self.event.sender.city = city
                    self.event.sender.save()
                    return f"Изменил город на {city.name}"
        else:
            if self.event.sender.city is not None:
                return f"Ваш город - {self.event.sender.city}"
            else:
                raise RuntimeWarning("Не знаю ваш город.\n"
                                     "/Город [название] - устанавливает пользователю город ")


def add_city_to_db(city_name):
    yandexgeo_api = YandexGeoAPI()
    city_info = yandexgeo_api.get_city_info_by_name(city_name)
    if not city_info:
        raise RuntimeWarning("Не смог найти координаты для города")
    city = CityModel.objects.filter(name=city_info['name'])
    if len(city) != 0:
        raise RuntimeWarning("Такой город уже есть")
    city_info['synonyms'] = city_info['name'].lower()
    timezonedb_api = TimezoneDBAPI()
    timezone_name = timezonedb_api.get_timezone_by_coordinates(city_info['lat'], city_info['lon'])
    if not timezone_name:
        raise RuntimeWarning("Не смог найти таймзону для города")
    timezone_obj, _ = TimeZone.objects.get_or_create(name=timezone_name)

    city_info['timezone'] = timezone_obj
    city = CityModel(**city_info)
    city.save()
    return city
