from threading import Thread

from django.contrib.auth.models import Group

from apps.bot.classes.Consts import Platform, Role
from apps.bot.classes.bots.CommonBot import CommonBot
from apps.bot.models import Users


class APIBot(CommonBot, Thread):
    def __init__(self):
        Thread.__init__(self)
        CommonBot.__init__(self, Platform.API)

    def get_user_by_id(self, user_id):
        api_user = self.user_model.filter(user_id=user_id)
        if len(api_user) > 0:
            api_user = api_user.first()
        else:
            # Если пользователь из fwd
            api_user = Users()
            api_user.user_id = user_id
            api_user.platform = self.platform

            api_user.save()

            group_user = Group.objects.get(name=Role.USER.name)
            api_user.groups.add(group_user)
            api_user.save()
        return api_user

    def get_chat_by_id(self, chat_id):
        pass

    def get_bot_by_id(self, bot_id):
        pass

    def listen(self):
        pass

    def send_message(self, peer_id, msg="ᅠ", attachments=None, keyboard=None, dont_parse_links=False, **kwargs):
        pass

    def upload_document(self, document, peer_id=None, title='Документ'):
        pass

    def upload_photos(self, images, max_count=10):
        pass
