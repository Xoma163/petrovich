from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import get_random_int


class Waifu(Command):
    name = "вайфу"
    name_tg = 'waifu'

    help_text = HelpText(
        commands_text="присылает несуществующую вайфу",
        help_texts=[
            HelpTextItem(Role.USER, [
                "[номер=рандом] - присылает несуществующую вайфу по номеру (0-100000)",
                "(слово) - присылает несуществующую вайфу вычисляя её номер"
            ])
        ]
    )

    def start(self) -> ResponseMessage:
        waifus_count = 100000
        if self.event.message.args:
            try:
                self.int_args = [0]
                self.parse_int()
                waifu_number = self.event.message.args[0]
                self.check_number_arg_range(waifu_number, 0, waifus_count)
            except PWarning:
                seed = self.event.message.args_str
                waifu_number = get_random_int(waifus_count, seed=seed)
        else:
            waifu_number = get_random_int(waifus_count)
        url = f"https://www.thiswaifudoesnotexist.net/example-{waifu_number}.jpg"
        attachment = self.bot.get_photo_attachment(url, peer_id=self.event.peer_id, filename="petrovich_waifu.png")

        if self.event.message.args:
            button = self.bot.get_button("Следующая", self.name, [waifu_number + 1])
        else:
            button = self.bot.get_button("Ещё", self.name)
        keyboard = self.bot.get_inline_keyboard([button])
        return ResponseMessage(ResponseMessageItem(text=waifu_number, attachments=[attachment], keyboard=keyboard))
