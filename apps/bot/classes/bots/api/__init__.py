from apps.bot.classes.bots import Bot
from apps.bot.classes.const.consts import Platform
from apps.bot.classes.const.exceptions import PError
from apps.bot.classes.event.api import APIEvent
from apps.bot.models import Profile


class APIBot(Bot):
    def __init__(self):
        Bot.__init__(self, Platform.API)

    def parse(self, raw_event):
        token = raw_event['token']
        try:
            raw_event['profile'] = Profile.objects.get(api_token=token)
        except Profile.DoesNotExist:
            raise PError('user for this token was not found')
        api_event = APIEvent(raw_event, self)
        return self.handle_event(api_event)
