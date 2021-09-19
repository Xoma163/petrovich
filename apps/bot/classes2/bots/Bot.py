import logging
from threading import Thread

import traceback

from apps.bot.classes2.Exceptions import PWarning, PError
from apps.bot.classes.common.CommonMethods import tanimoto
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

    def handle_message_wrap(self, event, send=True):
        message = self.handle_message(event)
        if send and message:
            self.parse_and_send_msgs(event.peer_id, message)
        return message

    # ToDo: проверка на забаненых куда-нибудь там в need_response
    def handle_message(self, event):
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
                msg = "Непредвиденная ошибка. Сообщите разработчику в группе или команда /баг"
                tb = traceback.format_exc()
                log_exception = {
                    'exception': str(e),
                    'result': msg
                }
                self.logger.error(log_exception, exc_info=tb)
                return msg

        if event.chat and not event.chat.need_reaction:
            return None

        similar_command = self.get_similar_command(event, COMMANDS)
        self.logger.debug({'result': similar_command})

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
                    tanimoto_current = tanimoto(event.command, name)
                    if tanimoto_current > tanimoto_max:
                        tanimoto_max = tanimoto_current
                        similar_command = name

        msg = f"Я не понял команды \"{event.command}\"\n"
        if similar_command and tanimoto_max != 0:
            msg += f"Возможно вы имели в виду команду \"{similar_command}\""
        return msg
