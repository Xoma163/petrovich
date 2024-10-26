from apps.bot.api.gpt.message import GPTMessages
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PSkip
from apps.bot.classes.event.event import Event
from apps.bot.classes.event.tg_event import TgEvent
from apps.bot.classes.messages.attachments.sticker import StickerAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.commands.gpt.gemini import Gemini
from apps.bot.commands.gpt.gwtf import GWTF
from apps.bot.commands.gpt_with_key.chatgpt import ChatGPT
from apps.bot.commands.gpt_with_key.wtf import WTF
from apps.bot.utils.utils import random_probability, random_event


class Turett(Command):
    conversation = True
    priority = 85
    name = 'туретт'

    # ACCEPT CHANCES
    MENTIONED_CHANCE = 1
    NOT_MENTIONED_CHANCE = 0.3

    # WEIGHTS
    STICKER_CHANCE = 10
    TEXT_CHANCE = 10
    GPT_CHANCE = 30
    GPT_WTF_CHANCE = 30
    REACTION_CHANCE = 20

    # TEXT SETTINGS
    TURETT_WORDS = [
        "Пошёл нахуй",
        "Пидор",
        "Бля",
        "ПИДАР",
        "ЕБЛАН",
        "МАТЬ ТВОЮ В КИНО ВОДИЛ",
        "ты не прогер",
        "А может тебе ещё и станцевать, долбоёб?",
        "отсоси потом проси",
        "Как же ты меня заебал",
        "ОТЪЕБИСЬ",
        "я тебе чё, бот ебаный?",
        "хуй, пизда из одного гнезда",
        "а на грудь тебе не насрать?",
        'ясно, долбоёб',
        'САСИ'
    ]

    # STICKER SETTINGS
    STICKER_SET_ID = "SamPriFle"

    # GPT SETTINGS
    MIN_TEXT_LEN = 10
    GPT_PROMPTS = [
        "Придумай мем в ответ на сообщение",
        "Расскажи анекдот в ответ на сообщение",
        "Перепиши сообщение в виде стихотворения",
        "Искаверкай сообщение",
        "Перепиши сообщение, как будто его писал сумасшедший"
    ]

    # WTF SETTINGS
    WTF_PROMPTS = [
        "Опиши переписку одной смешной или мемной фразой",
        "Подразни участников переписки",
        "Придумай шуточные диагнозы участникам переписки",
        "Придумай анекдот в тему переписки"
    ]
    WTF_MESSAGES_COUNT = 50

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.gpt_class = None
        self.wtf_class = None

    def accept(self, event: Event) -> bool:
        if event.is_notify:
            return False
        if event.chat and event.chat.settings.need_turett:
            chance = self.NOT_MENTIONED_CHANCE if event.chat.settings.no_mention else self.MENTIONED_CHANCE
            if random_probability(chance):
                return True
        return super().accept(event)

    def start(self) -> ResponseMessage:
        if isinstance(self.event.bot, TgBot):
            if self.event.message.command in self.full_names:
                rmi = self.handle_tg_event_with_mention()
            else:
                rmi = self.handle_tg_event()
        else:
            rmi = self.handle_event()
        return ResponseMessage(rmi)

    def handle_tg_event_with_mention(self) -> ResponseMessageItem:
        return self.get_gpt_wtf_text()

    def handle_tg_event(self) -> ResponseMessageItem:
        events = [self.get_text, self.get_sticker, self.get_gpt_text, self.get_gpt_wtf_text, self.set_reaction]
        weights = [self.TEXT_CHANCE, self.STICKER_CHANCE, self.GPT_CHANCE, self.GPT_WTF_CHANCE, self.REACTION_CHANCE]
        if len(self.event.message.clear_case) < self.MIN_TEXT_LEN and self.event.sender.check_role(Role.TRUSTED):
            events = [self.get_text, self.get_sticker, self.get_gpt_wtf_text, self.set_reaction]
            weights = [self.TEXT_CHANCE, self.STICKER_CHANCE, self.GPT_WTF_CHANCE, self.REACTION_CHANCE]
        method = random_event(events, weights)
        return method()

    def handle_event(self) -> ResponseMessageItem:
        return self.get_text()

    def get_sticker(self) -> ResponseMessageItem:
        stickers = self.event.bot.get_sticker_set(self.STICKER_SET_ID)
        random_sticker = random_event(stickers)
        tg_sticker = StickerAttachment()
        tg_sticker.parse_tg(random_sticker)
        return ResponseMessageItem(attachments=[tg_sticker])

    def get_text(self) -> ResponseMessageItem:
        if not self.event.sender.settings.use_swear:
            raise PSkip()
        answer = random_event(self.TURETT_WORDS)
        return ResponseMessageItem(text=answer)

    def get_gpt_text(self) -> ResponseMessageItem:
        self.event: TgEvent
        self._set_random_gpt_wtf_classes()

        prompt = random_event(self.GPT_PROMPTS)
        new_prompt = f"{prompt}:\n{self.event.message.clear}"

        gpt = self.gpt_class()
        gpt.bot = self.bot
        gpt.event = self.event
        messages = gpt.get_dialog(new_prompt)
        rmi = self._get_gpt_answer(messages)
        rmi.reply_to = self.event.message.id
        return rmi

    def get_gpt_wtf_text(self) -> ResponseMessageItem:
        self.event: TgEvent
        self._set_random_gpt_wtf_classes()

        prompt = random_event(self.WTF_PROMPTS)

        wtf = self.wtf_class()
        wtf.bot = self.bot
        wtf.event = self.event
        messages = wtf.get_conversation(self.WTF_MESSAGES_COUNT, prompt)

        answer = self._get_gpt_answer(messages)
        answer.reply_to = None
        return answer

    def _get_gpt_answer(self, messages: GPTMessages) -> ResponseMessageItem:
        gpt = self.gpt_class()
        gpt.bot = self.bot
        gpt.event = self.event
        return gpt.completions(messages, use_statistics=False)

    def set_reaction(self):
        self.event: TgEvent
        self.bot: TgBot
        reactions = ["💩", "🤡"]
        reaction = random_event(reactions)
        self.bot.set_message_reaction(self.event.chat.chat_id, self.event.message.id, reaction, True)
        raise PSkip()

    def _set_random_gpt_wtf_classes(self):
        classes = [
            [ChatGPT, WTF],
            [Gemini, GWTF]
        ]
        gpt_class, wtf_class = random_event(classes)
        self.gpt_class = gpt_class
        self.wtf_class = wtf_class
