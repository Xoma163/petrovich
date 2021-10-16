import logging
import traceback
from threading import Thread

from apps.bot.classes.common.CommonMethods import tanimoto
from apps.bot.classes2.Exceptions import PWarning, PError
from apps.bot.classes2.messages.ResponseMessage import ResponseMessage
from apps.bot.classes2.messages.ResponseMessageItem import ResponseMessageItem
from apps.bot.models import Users, Chat, Bot as BotModel


class Bot(Thread):
    def __init__(self, platform):
        Thread.__init__(self)

        self.platform = platform
        self.mentions = []
        self.user_model = Users.objects.filter(platform=self.platform.name)
        self.chat_model = Chat.objects.filter(platform=self.platform.name)
        self.bot_model = BotModel.objects.filter(platform=self.platform.name)

        self.logger = logging.getLogger(platform.value)

    def run(self):
        """
        Thread запуск основного тела команды
        """
        self.listen()

    def listen(self):
        """
        Получение новых событий и их обработка
        """
        pass

    def handle_event(self, event, send=True):
        try:
            event.setup_event()
            if not event.need_a_response():
                return
            message = self.route(event)
            if message:
                self.parse_and_send_msgs(event.peer_id, message, send)
        except Exception as e:
            print(str(e))
            tb = traceback.format_exc()
            print(tb)

    def send_response_message(self, rm: ResponseMessage):
        for msg in rm.messages:
            response = self.send_message(msg)
            if response.status_code != 200:
                error_msg = "Непредвиденная ошибка. Сообщите разработчику. Команда /баг"
                error_rm = ResponseMessage(error_msg, msg.peer_id).messages[0]
                self.logger.error({'result': error_msg, 'error': response.json()['description']})
                self.send_message(error_rm)

    def parse_and_send_msgs(self, peer_id, msgs, send=True) -> ResponseMessage:
        """
        Отправка сообщения от команды. Принимает любой формат
        """
        rm = ResponseMessage(msgs, peer_id)
        if send:
            self.send_response_message(rm)
        return rm

    def route(self, event):
        """
        Выбор команды и отправка данных о сообщении ей
        """
        self.logger.debug(event)

        from apps.bot.initial import COMMANDS
        for command in COMMANDS:
            try:
                if command.accept(event):
                    result = command.__class__().check_and_start(self, event)
                    self.logger.debug({'result': result})
                    return result
            except (PWarning, PError) as e:
                msg = str(e)
                getattr(self.logger, e.level)({'result': msg})
                return msg
            except Exception as e:
                msg = "Непредвиденная ошибка. Сообщите разработчику. Команда /баг"
                log_exception = {
                    'exception': str(e),
                    'result': msg
                }
                self.logger.error(log_exception, exc_info=traceback.format_exc())
                return msg

        if event.chat and not event.chat.need_reaction:
            return

        similar_command = self.get_similar_command(event, COMMANDS)
        self.logger.debug({'result': similar_command})
        return similar_command

    @staticmethod
    def get_similar_command(event, commands):
        """
        Получение похожей команды по неправильно введённой
        """
        similar_command = None
        tanimoto_max = 0
        user_groups = event.sender.get_list_of_role_names()
        for command in commands:
            if not command.full_names:
                continue

            # Выдача пользователю только тех команд, которые ему доступны
            command_access = command.access
            # ToDo: wtf?
            if isinstance(command_access, str):
                command_access = [command_access]
            if command_access.name not in user_groups:
                continue

            # Выдача только тех команд, у которых стоит флаг выдачи
            if not command.suggest_for_similar:
                continue

            for name in command.full_names:
                if name:
                    tanimoto_current = tanimoto(event.message.command, name)
                    if tanimoto_current > tanimoto_max:
                        tanimoto_max = tanimoto_current
                        similar_command = name

        msg = f"Я не понял команды \"{event.message.command}\"\n"
        if similar_command and tanimoto_max != 0:
            msg += f"Возможно вы имели в виду команду \"{similar_command}\""
        return msg

    def get_chat_by_id(self, chat_id) -> Chat:
        """
        Возвращает чат по его id
        """
        if chat_id > 0:
            chat_id *= -1
        tg_chat = self.chat_model.filter(chat_id=chat_id)
        if len(tg_chat) > 0:
            tg_chat = tg_chat.first()
        else:
            tg_chat = Chat(chat_id=chat_id, platform=self.platform.name)
            tg_chat.save()
        return tg_chat

    def send_message(self, rm: ResponseMessageItem):
        raise NotImplementedError
