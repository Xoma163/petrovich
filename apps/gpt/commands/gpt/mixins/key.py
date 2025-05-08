from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.gpt.models import GPTSettings
from apps.gpt.protocols import GPTCommandProtocol


class GPTKeyMixin(GPTCommandProtocol):
    KEY_HELP_TEXT_ITEMS = [
        HelpTextArgument("ключ (ключ)", "добавляет персональный API ключ"),
        HelpTextArgument("ключ удалить", "удаляет персональный API ключ"),
    ]

    KEEP_YOUR_SECRET_KEY_IN_SAFE = "Держите свой ключ в секрете. Я удалил ваше сообщение с ключом (или удалите сами если у меня нет прав). Добавьте его в личных сообщениях"

    # MENU

    def menu_key(self) -> ResponseMessageItem:
        """
        Установка/удаление персонального ключа ChatGPT
        """

        self.check_args(2)
        arg = self.event.message.args_case[1]

        key_field_name = self.provider.gpt_settings_key_field

        gpt_settings = getattr(self.event.sender, "gpt_settings", None)
        if not gpt_settings:
            gpt_settings = GPTSettings(profile=self.event.sender)

        if arg.lower() == "удалить":
            setattr(gpt_settings, key_field_name, "")
            gpt_settings.save()
            rmi = ResponseMessageItem(text="Удалил ваш ключ")
        else:
            if self.event.is_from_chat:
                self.bot.delete_messages(self.event.chat.chat_id, self.event.message.id)
                raise PWarning(self.KEEP_YOUR_SECRET_KEY_IN_SAFE)
            setattr(gpt_settings, key_field_name, arg)
            gpt_settings.save()
            rmi = ResponseMessageItem(text="Добавил новый ключ")

        return rmi

    # COMMON UTILS

    def check_key(self) -> ResponseMessage | None:
        settings_key_field = self.provider.gpt_settings_key_field

        # try:
        gpt_settings = getattr(self.event.sender, "gpt_settings", None)
        user_has_not_role_gpt = not self.event.sender.check_role(Role.GPT)
        user_has_not_personal_key = not (gpt_settings and getattr(gpt_settings, settings_key_field))

        if user_has_not_role_gpt and user_has_not_personal_key:
            if self.event.message.args[0] in ["ключ", "key"]:
                return ResponseMessage(self.menu_key())
            else:
                # ?
                raise PWarning(
                    f"Для использования {self.provider.name} укажите свой ключ (API_KEY) {self.bot.get_formatted_text_line('/gpt ключ (ключ)')}")
