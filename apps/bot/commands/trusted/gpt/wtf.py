from collections import OrderedDict
from typing import List

from apps.bot.classes.command import Command
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.event.event import Event
from apps.bot.classes.event.tg_event import TgEvent
from apps.bot.classes.messages.response_message import ResponseMessage
from apps.bot.commands.trusted.gpt.chatgpt import ChatGPT
from apps.bot.utils.cache import MessagesCache


class WTF(Command):
    name = "wtf"

    help_text = "обрабатывает сообщения в конфе через ChatGPT"
    help_texts = [
        "(prompt) [N=50] - обрабатывает последние N сообщений в конфе через ChatGPT по указанному prompt"
    ]
    args = 1
    access = Role.TRUSTED
    platforms = [Platform.TG]

    def start(self) -> ResponseMessage:
        last_arg = self.event.message.args[-1]
        try:
            n = int(last_arg)
            prompt = " ".join(self.event.message.args_case[:-1])
        except ValueError:
            n = 50
            prompt = self.event.message.args_str_case

        messages = self.get_conversation(n, prompt)

        gpt = ChatGPT()
        gpt.bot = self.bot
        gpt.event = self.event

        try:
            self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.TYPING)
            answer = gpt.text_chat(messages)
        finally:
            self.bot.stop_activity_thread()
        return answer

    def get_conversation(self, n: int, prompt: str, use_preprompt: bool = True) -> list:
        events = self.get_last_messages_as_events(n)
        result_message = []

        events = list(filter(lambda x: x.is_from_user and x.message.raw, events))

        last_user = events[0].sender
        messages_from_one_user = []

        len_events = len(events)
        for i, event in enumerate(events):
            text = event.message.raw
            if last_user != event.sender or i == len_events - 1:
                message_header = f"[{last_user.name}]"
                message_body = "\n".join(messages_from_one_user)
                message = f"{message_header}\n{message_body}"
                result_message.append(message)

                messages_from_one_user = []
                last_user = event.sender

            messages_from_one_user.append(text)

        messages = []
        preprompt = None
        if use_preprompt:
            if self.event.sender.gpt_preprompt:
                preprompt = self.event.sender.gpt_preprompt
            elif self.event.chat and self.event.chat.gpt_preprompt:
                preprompt = self.event.chat.gpt_preprompt
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
            # не <= потому что не берём последнее сообщение, которым зашли в эту команду :)
            if mid - message_id < n:
                try:
                    event = TgEvent({'message': message_body})
                    event.setup_event()
                except:
                    continue
                events.append(event)
        events = list(reversed(events))

        return events
