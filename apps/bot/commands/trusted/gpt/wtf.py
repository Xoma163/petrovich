from collections import OrderedDict
from itertools import groupby
from typing import List

from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.command import Command
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.event.event import Event
from apps.bot.classes.event.tg_event import TgEvent
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage
from apps.bot.commands.chatgpt import ChatGPT
from apps.bot.utils.cache import MessagesCache


class WTF(Command):
    name = "wtf"

    DEFAULT_PROMPT = "Я пришлю тебе переписку участников группы. Суммаризируй её, опиши, что произошло, о чём общались люди?"

    help_text = HelpText(
        commands_text="обрабатывает сообщения в конфе через ChatGPT",
        help_texts=[
            HelpTextItem(
                Role.TRUSTED, [
                    HelpTextItemCommand(
                        "(prompt) [N=50]",
                        "обрабатывает последние N сообщений в конфе через ChatGPT по указанному prompt")
                ])
        ],
        extra_text=f"prompt по умолчанию:\n{DEFAULT_PROMPT}"

    )

    args = 1
    platforms = [Platform.TG]
    gpt_key = True

    def start(self) -> ResponseMessage:

        last_arg = self.event.message.args[-1]
        try:
            n = int(last_arg)
            prompt = " ".join(self.event.message.args_case[:-1])
        except ValueError:
            n = 50
            prompt = self.event.message.args_str_case

        if not prompt:
            prompt = self.DEFAULT_PROMPT

        with ChatActivity(self.bot, ActivitiesEnum.TYPING, self.event.peer_id):
            messages = self.get_conversation(n, prompt)

        gpt = ChatGPT()
        gpt.bot = self.bot
        gpt.event = self.event

        with ChatActivity(self.bot, ActivitiesEnum.TYPING, self.event.peer_id):
            answer = gpt.text_chat(messages)
        return ResponseMessage(answer)

    @staticmethod
    def _format_groupped_messages(last_user, messages_from_one_user):
        message_header = f"[{last_user.name}]"
        message_body = "\n".join(messages_from_one_user)
        message = f"{message_header}\n{message_body}"
        return message

    def get_conversation(self, n: int, prompt: str, use_preprompt: bool = True) -> list:
        events = self.get_last_messages_as_events(n)
        result_message = []

        events = list(filter(lambda x: x.is_from_user and x.message.raw, events))
        for sender, events in groupby(events, key=lambda x: x.sender):
            messages_from_one_user = []
            for event in events:
                messages_from_one_user.append(event.message.raw)
            message = self._format_groupped_messages(sender, messages_from_one_user)
            result_message.append(message)

        messages = []
        preprompt = None
        if use_preprompt:
            preprompt = ChatGPT.get_preprompt(self.event.sender, self.event.chat, ChatGPT.PREPROMPT_PROVIDER)
        if preprompt:
            messages.append({"role": "system", "content": preprompt})
        messages.append({'role': "user", 'content': prompt})
        messages.append({'role': "user", 'content': "\n".join(result_message)})
        return messages

    def get_last_messages_as_events(self, n: int) -> List[Event]:
        mid = self.event.message.id
        peer_id = self.event.peer_id

        mc = MessagesCache(peer_id)
        data = mc.get_messages()
        messages = OrderedDict(sorted(data.items(), key=lambda x: x[0], reverse=True))
        events = []

        for message_id, message_body in messages.items():
            # не берём последнее сообщение, которым зашли в эту команду :)
            if 1 <= mid - message_id < n + 1:
                try:
                    event = TgEvent({'message': message_body})
                    event.setup_event()
                except Exception:
                    continue
                events.append(event)
        events = list(reversed(events))

        return events
