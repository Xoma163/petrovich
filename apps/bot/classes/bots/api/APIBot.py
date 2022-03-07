from apps.bot.classes.bots.Bot import Bot as CommonBot
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PError
from apps.bot.classes.events.APIEvent import APIEvent
from apps.bot.models import Profile


class APIBot(CommonBot):
    def __init__(self):
        CommonBot.__init__(self, Platform.API)

    def parse(self, raw_event):
        token = raw_event['token']
        try:
            raw_event['profile'] = Profile.objects.get(api_token=token)
        except Profile.DoesNotExist:
            raise PError('user for this token was not found')
        api_event = APIEvent(raw_event, self)
        return self.handle_event(api_event)
