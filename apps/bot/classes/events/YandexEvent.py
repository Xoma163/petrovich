from apps.bot.classes.events.Event import Event


class YandexEvent(Event):
    def setup_event(self, is_fwd=False):
        user_id = self.raw['session']['user']['user_id']
        text = self.raw['request']['command']

        self.sender = self.bot.get_user_by_id(user_id)
        self.is_from_user = True
        self.is_from_pm = True
        self.set_message(text)
