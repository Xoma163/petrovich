from threading import Thread

from vk_api import VkUpload, VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from apps.bot.bots.CommonBot import CommonBot
from apps.bot.bots.VkUser import VkUser
from petrovich.settings import env


class VkBot(CommonBot, Thread):
    def __init__(self):
        CommonBot.__init__(self)
        Thread.__init__(self)

        self._TOKEN = env.str('VK_BOT_TOKEN')
        self.group_id = env.str('VK_BOT_GROUP_ID')
        vk_session = VkApi(token=self._TOKEN, api_version="5.107", config_filename="secrets/vk_bot_config.json")
        self.longpoll = MyVkBotLongPoll(vk_session, group_id=self.group_id)
        self.upload = VkUpload(vk_session)
        self.vk = vk_session.get_api()
        self.mentions = env.list('VK_BOT_MENTIONS')

        self.vk_user = VkUser()

        self.BOT_CAN_WORK = True
        self.DEBUG = False
        self.DEVELOP_DEBUG = False

    def get_user_by_id(self, user_id):
        # vk_user = VkUser.objects.filter(user_id=user_id)
        # if len(vk_user) > 0:
        #     vk_user = vk_user.first()
        # else:
        #     # Прозрачная регистрация
        #     user = self.vk.users.get(user_id=user_id, lang='ru', fields='sex, bdate, city, screen_name')[0]
        #     vk_user = VkUserModel()
        #     vk_user.user_id = user_id
        #     vk_user.name = user['first_name']
        #     vk_user.surname = user['last_name']
        #     if 'sex' in user:
        #         vk_user.gender = user['sex']
        #     if 'bdate' in user:
        #         vk_user.birthday = self.parse_date(user['bdate'])
        #     if 'city' in user:
        #         from apps.service.models import City
        #         city_name = user['city']['title']
        #         city = City.objects.filter(name=city_name)
        #         if len(city) > 0:
        #             city = city.first()
        #         else:
        #             try:
        #                 city = add_city_to_db(city_name)
        #             except Exception:
        #                 city = None
        #         vk_user.city = city
        #     else:
        #         vk_user.city = None
        #     if 'screen_name' in user:
        #         vk_user.nickname = user['screen_name']
        #     vk_user.save()
        #     group_user = Group.objects.get(name=Role.USER.name)
        #     vk_user.groups.add(group_user)
        #     vk_user.save()
        # return vk_user
        pass

    def listen(self):
        for event in self.longpoll.listen():
            try:
                # Если пришло новое сообщение
                if event.type == VkBotEventType.MESSAGE_NEW:
                    vk_event = {
                        'from_user': event.from_user,
                        'chat_id': event.chat_id,
                        'user_id': event.message.from_id,
                        'peer_id': event.message.peer_id,
                        'message': {
                            # 'id': event.message.id,
                            'text': event.message.text,
                            'payload': event.message.payload,
                            'attachments': event.message.attachments,
                            'action': event.message.action
                        },
                        'fwd': None
                    }
                    # Сообщение либо мне в лс, либо упоминание меня, либо есть аудиосообщение, либо есть экшн
                    if not self.need_a_response(vk_event):
                        continue

                    # Обработка вложенных сообщений в vk_event['fwd']. reply и fwd для вк это разные вещи.
                    if event.message.reply_message:
                        vk_event['fwd'] = [event.message.reply_message]
                    elif len(event.message.fwd_messages) != 0:
                        vk_event['fwd'] = event.message.fwd_messages

                    # Узнаём пользователя
                    if vk_event['user_id'] > 0:
                        vk_event['sender'] = self.get_user_by_id(vk_event['user_id'])
                    else:
                        self.send_message(vk_event['peer_id'], "Боты не могут общаться с Петровичем :(")
                        continue

                    print('message')
            except:
                pass


class MyVkBotLongPoll(VkBotLongPoll):

    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as e:
                error = {'exception': f'Longpoll Error (VK): {str(e)}'}
                # logger.error(error)
