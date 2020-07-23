import datetime

from django.http import JsonResponse

from apps.bot.APIs.YandexGeoAPI import YandexGeoAPI
from apps.bot.classes.bots.CommonBot import get_bot_by_platform
from apps.bot.classes.common.CommonMethods import localize_datetime
from apps.bot.models import Users
from apps.db_logger.models import MovementLog


def json_response(params):
    return JsonResponse(params, json_dumps_params={'ensure_ascii': False})


def get_somewhere(lat, lon):
    yandexgeo_api = YandexGeoAPI()
    address = yandexgeo_api.get_address(lat, lon)

    if address is not None:
        msg = f"Я нахожусь примерно тут:\n" \
              f"{address}\n"
    else:
        msg = ""
    msg += f"Позиция на карте:\n" \
           f"https://yandex.ru/maps/?ll={lon}%2C{lat}&mode=search&text={lat}%2C%20{lon}&z=16\n"
    return msg


def get_another_position(author, where):
    positions = {
        "home": {0: "Выхожу из дома", 1: "Я дома", "count": 0},
        "work": {0: "Я на работе", 1: "Выхожу с работы", "count": 0},
        "university": {0: "Я в универе", 1: "Выхожу из универа", "count": 0},
    }

    today = localize_datetime(datetime.datetime.utcnow(), author.city.timezone.name)
    today_logs = MovementLog.objects.filter(date__year=today.year, date__month=today.month, date__day=today.day,
                                            author=author)
    for today_log in today_logs:
        if today_log.event in positions:
            positions[today_log.event]['count'] += 1
    msg = positions[where][positions[where]['count'] % 2]
    return msg


# ToDo собрать в одно место все проверки
def where_is_me(request):
    log = MovementLog()

    where = request.GET.get('where', None)
    if not where:
        log.msg = "Where is None"
        log.save()
        return json_response({'status': 'error', 'message': log.msg})
    log.where = where

    imei = request.GET.get('imei', None)
    if not imei:
        log.msg = "IMEI is None"
        log.save()
        return json_response({'status': 'error', 'message': log.msg})
    log.imei = imei

    author = Users.objects.filter(imei=imei).first()
    if not author:
        log.msg = "Author is None"
        log.save()
        return json_response({'status': 'error', 'message': log.msg})

    recipients = author.send_notify_to.all()
    if not recipients:
        log.msg = "Recipients is None"
        log.save()
        return json_response({'status': 'error', 'message': log.msg})

    if where == 'somewhere':
        lat = request.GET.get('lat', None)
        lon = request.GET.get('lon', None)
        if not lat or not lon:
            log.msg = "Lat or Lon is None"
            log.save()
            return json_response({'status': 'error', 'message': log.msg})
        msg = get_somewhere(lat, lon)
    elif where in ['home', 'work', 'university']:
        msg = get_another_position(author, where)
    else:
        log.msg = "Не найдено такое событие(?)"
        log.save()
        return json_response({'status': 'error', 'message': log.msg})

    msg += "\n%s" % author.name
    log.msg = msg
    log.save()
    for recipient in recipients:
        bot = get_bot_by_platform(recipient.platform)()
        bot.parse_and_send_msgs(recipient.user_id, msg)
    return json_response({'status': 'success'})
