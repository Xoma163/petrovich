from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.attachments.sticker import StickerAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import random_probability, random_event


class Turett(Command):
    conversation = True
    priority = 85

    MENTIONED_CHANCE = 1
    NOT_MENTIONED_CHANCE = 0.3
    STICKER_CHANCE = 50

    STICKER_SET_ID = "SamPriFle"
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

    def accept(self, event: Event) -> bool:
        if event.chat and event.chat.need_turett and event.chat.use_swear:
            chance = self.NOT_MENTIONED_CHANCE if event.chat.mentioning else self.MENTIONED_CHANCE
            if random_probability(chance):
                return True
        return False

    def start(self) -> ResponseMessage:
        if isinstance(self.event.bot, TgBot):
            if random_probability(self.STICKER_CHANCE):
                rmi = self.get_text()
            else:
                rmi = self.get_sticker()
        else:
            rmi = self.get_text()
        return ResponseMessage(rmi)

    def get_sticker(self) -> ResponseMessageItem:
        stickers = self.event.bot.get_sticker_set(self.STICKER_SET_ID)
        random_sticker = random_event(stickers)
        tg_sticker = StickerAttachment()
        tg_sticker.parse_tg(random_sticker)
        return ResponseMessageItem(attachments=[tg_sticker])

    def get_text(self) -> ResponseMessageItem:
        answer = random_event(self.TURETT_WORDS)
        return ResponseMessageItem(text=answer)
