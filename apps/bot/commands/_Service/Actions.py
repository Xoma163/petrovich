from apps.bot.classes.Consts import Platform
from apps.bot.classes.Exceptions import PError
from apps.bot.classes.common.CommonCommand import CommonCommand
from petrovich.settings import env


class Actions(CommonCommand):
    def __init__(self):
        super().__init__([None], priority=100)

    def accept(self, event):
        if event.action:
            return True
        return False

    def start(self):
        if self.event.action:
            # По приглашению пользователя
            if self.event.action['type'] in ['chat_invite_user', 'chat_invite_user_by_link']:
                for _id in self.event.action['member_ids']:
                    if _id > 0:
                        user = self.bot.get_user_by_id(_id)
                        self.bot.add_chat_to_user(user, self.event.chat)
                    else:
                        if self.event.platform == Platform.VK:
                            bot_group_id = -env.int('VK_BOT_GROUP_ID')
                        elif self.event.platform == Platform.TG:
                            bot_group_id = -env.int('TG_BOT_GROUP_ID')
                        else:
                            raise PError("Неизвестный клиент")
                        if _id == bot_group_id:
                            if self.event.chat.admin is None:
                                self.event.chat.admin = self.event.sender
                                self.event.chat.save()
                                return f"Администратором конфы является {self.event.sender}\n" \
                                       f"Задайте имя конфы:\n" \
                                       "/конфа {Название конфы}"
                            else:
                                return "Давненько не виделись!"
                        else:
                            self.bot.get_bot_by_id(_id)
            # По удалению пользователя
            elif self.event.action['type'] == 'chat_kick_user':
                if self.event.action['member_id'] > 0:
                    user = self.bot.get_user_by_id(self.event.action['member_id'])
                    self.bot.remove_group_from_user(user, self.event.chat)
            # По изменению чата конфы
            # elif self.event.action['type'] == 'chat_title_update':
            #     self.event.chat.name = self.event.action['text']
            #     self.event.chat.save()
