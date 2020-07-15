from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_random_int


class Waifu(CommonCommand):
    def __init__(self):
        names = ["вайфу"]
        help_text = "Вайфу - присылает несуществующую вайфу"
        detail_help_text = "Вайфу [номер=рандом] - присылает несуществующую вайфу по номеру (0-100000)\n" \
                           "Вайфу (слово) - присылает несуществующую вайфу вычисляя её номер"
        super().__init__(names, help_text, detail_help_text, platforms=['vk', 'tg'])

    def start(self):
        WAIFUS_COUNT = 100000
        if self.event.args:
            try:
                self.int_args = [0]
                self.parse_int()
                waifu_number = self.event.args[0]
                self.check_number_arg_range(waifu_number, 0, WAIFUS_COUNT)
            except RuntimeError:
                seed = " ".join(self.event.args)
                waifu_number = get_random_int(WAIFUS_COUNT, seed=seed)
        else:
            waifu_number = get_random_int(WAIFUS_COUNT)
        URL = f"https://www.thiswaifudoesnotexist.net/example-{waifu_number}.jpg"
        attachment = self.bot.upload_photos(URL)

        if self.event.args:
            keyboard = self.bot.get_inline_keyboard(self.names[0], "Следующая", args={"waifu_number": waifu_number + 1})
        else:
            keyboard = self.bot.get_inline_keyboard(self.names[0])
        return {"msg": waifu_number, "attachments": attachment, "keyboard": keyboard}
