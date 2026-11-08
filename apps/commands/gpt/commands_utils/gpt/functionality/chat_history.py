from collections import OrderedDict
from itertools import groupby

from apps.bot.core.chat_action_sender import ChatActionSender
from apps.bot.core.chat_actions import ChatActionEnum
from apps.bot.core.event.event import Event
from apps.bot.core.event.telegram.tg_event import TgEvent
from apps.bot.core.messages.response_message import ResponseMessageItem
from apps.bot.models import User
from apps.commands.gpt.messages.base import GPTMessages
from apps.commands.gpt.messages.consts import GPTMessageRole
from apps.commands.gpt.protocols import GPTCommandProtocol
from apps.commands.help_text import HelpTextArgument
from apps.shared.exceptions import PWarning
from apps.shared.utils.cache import MessagesCache


class GPTChatHistoryFunctionality(GPTCommandProtocol):
    DEFAULT_PROMPT = (
        "Я пришлю тебе переписку участников группы. Суммаризируй её, опиши, что произошло, о чём общались люди?"
    )
    DEFAULT_N = 50
    CHAT_HISTORY_HELP_TEXT_ITEMS = [
        HelpTextArgument(
            f"wtf [prompt] [N={DEFAULT_N}]", "обрабатывает последние N сообщений в конфе через GPT по указанному prompt"
        ),
        HelpTextArgument(
            "wtf [prompt] (пересланное сообщение)",
            "обрабатывает последние сообщения до пересланного в конфе через GPT по указанному prompt",
        ),
    ]

    def menu_chat_history(self) -> ResponseMessageItem:
        n, prompt = self._get_n_and_prompt()

        with ChatActionSender(self.bot, ChatActionEnum.TYPING, self.event.peer_id, self.event.message_thread_id):
            messages = self.get_conversation(n, prompt)

        return self.completions(messages)

    def _get_n_and_prompt(self) -> tuple[int, str]:
        args = self.event.message.args_case[1:]
        prompt = " ".join(args)
        if self.event.fwd:
            last_message_id = self.event.fwd[0].message.id
            current_message_id = self.event.message.id
            n = current_message_id - last_message_id
        else:
            n = self.DEFAULT_N
            last_arg = args[-1] if args else ""
            explicit_n = last_arg.lower().startswith("n=")
            try:
                n = int(last_arg[2:] if explicit_n else last_arg)
                prompt = " ".join(args[:-1])
            except ValueError:
                if explicit_n:
                    raise PWarning("N должно быть положительным целым числом")

        if n <= 0:
            raise PWarning("N должно быть положительным целым числом")

        if not prompt:
            prompt = self.DEFAULT_PROMPT
        return n, prompt

    @staticmethod
    def _format_groupped_messages(last_user, messages_from_one_user):
        message_header = f"[{last_user.name}]"
        message_body = "\n".join(messages_from_one_user)
        message = f"{message_header}\n{message_body}"
        return message

    def get_conversation(self, n: int, prompt: str) -> GPTMessages:
        events = self.get_last_messages_as_events(n)
        result_message = []

        events = list(filter(lambda x: x.is_from_user and x.message.raw, events))
        for sender, events in groupby(events, key=lambda x: x.sender):
            messages_from_one_user = []
            for event in events:
                messages_from_one_user.append(event.message.raw)
            message = self._format_groupped_messages(sender, messages_from_one_user)
            result_message.append(message)

        preprompt = self.get_preprompt(
            self.event.sender,
            self.event.chat,
        )
        history: GPTMessages = self.provider.messages_class()
        if preprompt:
            history.add_message(GPTMessageRole.SYSTEM, preprompt.text)
        history.add_message(GPTMessageRole.USER, prompt)
        history.add_message(GPTMessageRole.USER, "\n".join(result_message))
        return history

    def get_last_messages_as_events(self, n: int) -> list[Event]:
        mid = self.event.message.id
        peer_id = self.event.peer_id

        mc = MessagesCache(peer_id)
        data = mc.get_messages()
        messages = OrderedDict(sorted(data.items(), key=lambda x: x[0], reverse=True))
        events = []

        users = {}
        for message_id, message_body in messages.items():
            # не берём последнее сообщение, которым зашли в эту команду :)
            if 1 <= mid - message_id < n + 1:
                try:
                    event = TgEvent({"message": message_body}, use_db=False)
                    event.setup_event(use_db=False)

                    user_id = event.user_id
                    if user_id not in users:
                        try:
                            users[user_id] = User.objects.get(user_id=user_id).profile
                        except User.DoesNotExist:
                            users[user_id] = None

                    event.sender = users[user_id]

                except Exception:
                    continue
                events.append(event)
        events = list(reversed(events))

        return events
