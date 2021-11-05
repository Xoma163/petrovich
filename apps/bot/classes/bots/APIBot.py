from apps.bot.classes.bots.Bot import Bot as CommonBot
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PError
from apps.bot.classes.events.APIEvent import APIEvent
from apps.bot.models import Users


class APIBot(CommonBot):
    def __init__(self):
        CommonBot.__init__(self, Platform.API)

    def parse(self, raw_event):
        token = raw_event['token']
        try:
            self.user_model.get(user_id=token)
        except Users.DoesNotExist:
            raise PError('user for this token was not found')
        ya_event = APIEvent(raw_event, self)
        return self.handle_event(ya_event)
