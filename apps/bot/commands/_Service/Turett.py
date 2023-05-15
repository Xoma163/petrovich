from apps.bot.classes.Command import Command
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.messages.attachments.StickerAttachment import StickerAttachment
from apps.bot.utils.utils import random_probability, random_event


class Turett(Command):
    MENTIONED_CHANCE = 1
    NOT_MENTIONED_CHANCE = 0.3
    STICKER_CHANCE = 50
    conversation = True
    priority = 85

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

    def accept(self, event):
        if event.chat and event.chat.need_turett and event.chat.use_swear:
            self.send_turett(event)
        return False

    def start(self):
        pass

    def send_turett(self, event):
        chance = self.NOT_MENTIONED_CHANCE if event.chat.mentioning else self.MENTIONED_CHANCE
        if random_probability(chance):
            if isinstance(event.bot, TgBot):
                if random_probability(self.STICKER_CHANCE):
                    msg = random_event(self.TURETT_WORDS)
                else:
                    stickers = event.bot.get_sticker_set("SamPriFle")
                    random_sticker = random_event(stickers)
                    tg_sticker = StickerAttachment()
                    tg_sticker.parse_tg(random_sticker)
                    msg = {'attachments': tg_sticker}
            else:
                msg = random_event(self.TURETT_WORDS)
            event.bot.parse_and_send_msgs(msg, event.peer_id, event.message_thread_id)
