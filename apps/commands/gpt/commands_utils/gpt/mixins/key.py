from apps.bot.core.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.commands.gpt.api.base import GPTAPI
from apps.commands.gpt.enums import GPTProviderEnum
from apps.commands.gpt.models import ProfileGPTSettings
from apps.commands.gpt.protocols import GPTCommandProtocol
from apps.commands.gpt.utils import user_has_api_key
from apps.commands.help_text import HelpTextArgument
from apps.shared.exceptions import PWarning


class GPTKeyMixin(GPTCommandProtocol):
    KEY_HELP_TEXT_ITEMS = [
        HelpTextArgument("ключ (ключ)", "добавляет персональный API ключ"),
        HelpTextArgument("ключ удалить", "удаляет персональный API ключ"),
    ]

    KEEP_YOUR_SECRET_KEY_IN_SAFE = "Держите свой ключ в секрете. Я удалил ваше сообщение с ключом (или удалите сами если у меня нет прав)"
    PROVIDE_API_KEY_TEMPLATE = "Для использования {provider_name} укажите свой ключ (API_KEY)\n" \
                               "{command_name} ключ (ключ)"

    # MENU

    def menu_key(self) -> ResponseMessageItem:
        """
        Установка/удаление персонального ключа ChatGPT
        """

        self.check_args(2)
        arg = self.event.message.args_case[1]

        profile_gpt_settings = self.get_profile_gpt_settings()

        if arg.lower() in ["удалить", "сброс", "сбросить", "delete", "reset"]:
            profile_gpt_settings.set_key("")
            profile_gpt_settings.save()
            rmi = ResponseMessageItem(text="Удалил ваш ключ")
        else:
            if self.event.is_from_chat:
                self.bot.delete_messages(self.event.chat.chat_id, self.event.message.id)
                self._set_key(profile_gpt_settings, arg)
                raise PWarning(self.KEEP_YOUR_SECRET_KEY_IN_SAFE)
            self._set_key(profile_gpt_settings, arg)
            rmi = ResponseMessageItem(text="Добавил новый ключ")

        return rmi

    # COMMON UTILS

    def check_key(self) -> ResponseMessage | None:
        has_access = user_has_api_key(self.event.sender, self.provider)
        # Если у пользователя нет персонального ключа, тогда единственное, что мы ему даём - добавить ключ
        if not has_access:
            if self.event.message.args and self.event.message.args[0] in ["ключ", "key"]:
                return ResponseMessage(self.menu_key())
            else:
                error_msg = self.PROVIDE_API_KEY_TEMPLATE.format(
                    provider_name=self.provider.type_enum,
                    command_name=self.bot.get_formatted_text_line(f'/{self.name}')
                )
                raise PWarning(error_msg)
        return None

    @staticmethod
    def raise_no_access_exception(gpt_type_enum: GPTProviderEnum, command_name: str) -> None:
        error_msg = GPTKeyMixin.PROVIDE_API_KEY_TEMPLATE.format(
            provider_name=gpt_type_enum,
            command_name=command_name
        )
        raise PWarning(error_msg)

    # UTILS

    def _set_key(self, profile_gpt_settings: ProfileGPTSettings, api_key: str):
        gpt_api: GPTAPI = self.provider.api_class(
            api_key=api_key,
            log_filter=self.event.log_filter,
        )
        if not gpt_api.check_key():
            raise PWarning("Невалидный ключ")
        profile_gpt_settings.set_key(api_key)
        profile_gpt_settings.save()
