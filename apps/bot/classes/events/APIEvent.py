from apps.bot.classes.events.Event import Event


class APIEvent(Event):
    def setup_event(self, is_fwd=False):
        user_id = self.raw['token']
        text = self.raw['text']

        self.user = self.bot.get_user_by_id(user_id)
        # ToDo
        self.sender = None
        self.is_from_user = True
        self.is_from_pm = True
        self.set_message(text)
