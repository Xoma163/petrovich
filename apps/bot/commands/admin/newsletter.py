from typing import Tuple

from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.const.exceptions import PError
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.models import Profile


class Newsletter(Command):
    name = "рассылка"

    help_text = HelpText(
        commands_text="запускает рассылку по подписчикам",
        help_texts=[
            HelpTextItem(Role.ADMIN, [
                HelpTextItemCommand("(команда)", "запускает любую команду на сервере")
            ])
        ]
    )

    access = Role.ADMIN
    mentioned = True
    pm = True
    args = 1
    platforms = [Platform.TG]

    def start(self) -> ResponseMessage:
        arg0 = self.event.message.args[0]

        if arg0 in ["подтвердить"]:
            return self.start_newsletter()
        else:
            return self.prepare_message()

    def start_newsletter(self) -> ResponseMessage:
        raw_message = self.event.raw['callback_query']['message']
        text = raw_message['text']
        entities = raw_message['entities']

        subscribers = Profile.objects.filter(settings__is_newsletter_subscriber=True)

        rm = ResponseMessage(delay=1)
        rm.messages.append(ResponseMessageItem(text="Запустил рассылку"))

        for subscriber in subscribers:
            rmi = ResponseMessageItem(
                text=text,
                entities=entities,
                peer_id=subscriber.get_tg_user().user_id
            )
            rm.messages.append(rmi)

        rm.messages.append(ResponseMessageItem(text="Закончил рассылку"))

        return rm

    def prepare_message(self) -> ResponseMessage:
        answer = "Новостная рассылка.\n\n"
        text, entities = self._get_text(len(answer))
        button = self.bot.get_button("Подтвердить", self.name, ["подтвердить"])
        keyboard = self.bot.get_inline_keyboard([button])

        answer = f"{answer}{text}"
        rmi1 = ResponseMessageItem(
            text=answer,
            entities=entities,
            keyboard=keyboard
        )

        subscribers = Profile.objects.filter(settings__is_newsletter_subscriber=True)
        subscribers_str = "\n".join([str(x) for x in subscribers])

        answer = f"Сообщение будет отправлено следующим пользователям:\n{subscribers_str}"
        rmi2 = ResponseMessageItem(
            text=answer
        )

        return ResponseMessage([rmi1, rmi2])

    def _get_text(self, entities_offset=0) -> Tuple[str, list]:
        text = self.event.message.raw
        entities = self.event.message.entities

        total_delete_len = 0
        if self.event.message.has_command_symbols:
            text = text[1:]
            total_delete_len += 1

        text_to_delete = f"{self.event.message.command}\n"
        len_text_to_delete = len(text_to_delete)
        index = text.find(text_to_delete)
        if index != 0:
            raise PError("Ошибка. Не смог вырезать сообщение для рассылки")
        text = text[len_text_to_delete:]
        total_delete_len += len_text_to_delete

        for i, _ in enumerate(entities):
            entities[i]['offset'] -= total_delete_len - entities_offset
        return text, entities
