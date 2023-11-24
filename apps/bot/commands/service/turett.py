from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.event.event import Event
from apps.bot.classes.event.tg_event import TgEvent
from apps.bot.classes.messages.attachments.sticker import StickerAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.commands.trusted.gpt.chatgpt import ChatGPT
from apps.bot.commands.trusted.gpt.wtf import WTF
from apps.bot.utils.utils import random_probability, random_event


class Turett(Command):
    conversation = True
    priority = 85

    # ACCEPT CHANCES
    MENTIONED_CHANCE = 1
    NOT_MENTIONED_CHANCE = 0.3

    # WEIGHTS
    STICKER_CHANCE = 15
    TEXT_CHANCE = 15
    GPT_CHANCE = 35
    GPT_WTF_CHANCE = 35

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
    GPT_PROMTS = [
        "Придумай мем в ответ на сообщение",
        "Расскажи анекдот в ответ на сообщение",
        "Перепиши сообщение в виде стихотворения",
        "Искаверкай сообщение",
        "Перепиши сообщение, как будто его писал сумасшедший"
    ]

    # WTF SETTINGS
    WTF_PROMTS = [
        "Опиши переписку одной смешной или мемной фразой",
        "Подразни участников переписки",
        "Придумай шуточные диагнозы участникам переписки",
        "Придумай анекдот в тему переписки"
    ]
    WTF_MESSAGES_COUNT = 50

    def accept(self, event: Event) -> bool:
        if event.chat and event.chat.need_turett and event.chat.use_swear:
            chance = self.NOT_MENTIONED_CHANCE if event.chat.mentioning else self.MENTIONED_CHANCE
            if random_probability(chance):
                return True
        return False

    def start(self) -> ResponseMessage:
        if isinstance(self.event.bot, TgBot):
            rmi = self.handle_tg_event()
        else:
            rmi = self.handle_event()
        return ResponseMessage(rmi)

    def handle_tg_event(self):
        events = [self.get_text, self.get_sticker, self.get_gpt_text, self.get_gpt_wtf_text]
        weights = [self.TEXT_CHANCE, self.STICKER_CHANCE, self.GPT_CHANCE, self.GPT_WTF_CHANCE]
        if len(self.event.message.clear_case) < 10:
            events = [self.get_text, self.get_sticker]
            weights = [self.TEXT_CHANCE, self.STICKER_CHANCE]
        method = random_event(events, weights)
        return method()

    def handle_event(self):
        return self.get_text()

    def get_sticker(self) -> ResponseMessageItem:
        stickers = self.event.bot.get_sticker_set(self.STICKER_SET_ID)
        random_sticker = random_event(stickers)
        tg_sticker = StickerAttachment()
        tg_sticker.parse_tg(random_sticker)
        return ResponseMessageItem(attachments=[tg_sticker])

    def get_text(self) -> ResponseMessageItem:
        answer = random_event(self.TURETT_WORDS)
        return ResponseMessageItem(text=answer)

    def get_gpt_text(self) -> ResponseMessageItem:
        self.event: TgEvent

        promt = random_event(self.GPT_PROMTS)
        new_promt = f"{promt}:\n{self.event.message.clear}"

        messages = ChatGPT.get_dialog(self.event, new_promt, use_prepromt=False)
        return self._get_gpt_answer(messages)

    def get_gpt_wtf_text(self) -> ResponseMessageItem:
        self.event: TgEvent

        promt = random_event(self.WTF_PROMTS)

        wtf = WTF()
        wtf.bot = self.bot
        wtf.event = self.event
        messages = wtf.get_conversation(self.WTF_MESSAGES_COUNT, promt, use_prepromt=False)

        return self._get_gpt_answer(messages)

    def _get_gpt_answer(self, messages: list):
        chat_gpt = ChatGPT()
        chat_gpt.bot = self.bot
        chat_gpt.event = self.event
        rmi = chat_gpt.text_chat(messages).messages[0]
        rmi.reply_to = self.event.message.id
        return rmi
