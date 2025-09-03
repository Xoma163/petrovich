from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.gpt.enums import GPTReasoningEffortLevel, GPTVerbosityLevel
from apps.gpt.protocols import GPTCommandProtocol


class GPT5SettingsMixin(GPTCommandProtocol):
    GPT_5_SETTINGS_HELP_TEXT_ITEMS = [
        HelpTextArgument(
            "gpt_5_reasoning (high/medium/low/minimal)",
            "устанавливает уровень рассуждений для моделей семейства GPT-5"
        ),
        HelpTextArgument(
            "gpt_5_reasoning удалить",
            "удаляет настройку"
        ),
        HelpTextArgument(
            "gpt_5_verbosity (high/medium/low)",
            "устанавливает уровень многословности для моделей семейства GPT-5"
        ),
        HelpTextArgument(
            "gpt_5_verbosity удалить",
            "удаляет настройку"
        )
    ]

    def reasoning(self) -> ResponseMessageItem:
        try:
            self.check_args(2)
            if self.event.message.args[1] in ["удалить", "сброс", "сбросить", "delete", "reset"]:
                return self.delete_reasoning()
            return self.set_reasoning()
        except:
            return self.get_reasoning()

    def set_reasoning(self) -> ResponseMessageItem:
        user_value = self.event.message.args[1]
        available_levels = [effort_level.value for effort_level in GPTReasoningEffortLevel]  # noqa
        if user_value not in available_levels:
            available_levels_str = ", ".join(available_levels)
            raise PWarning(f"Уровня {user_value} нет среди доступных.\nДоступные уровни: {available_levels_str}")

        profile_settings = self.get_profile_gpt_settings()
        profile_settings.gpt_5_settings_reasoning_effort_level = user_value
        profile_settings.save()
        answer = f"Установил уровень рассуждений {user_value} для моделей семейства GPT-5"
        return ResponseMessageItem(text=answer)

    def get_reasoning(self) -> ResponseMessageItem:
        profile_settings = self.get_profile_gpt_settings()
        if profile_settings.gpt_5_settings_reasoning_effort_level:
            value = profile_settings.gpt_5_settings_reasoning_effort_level
        else:
            value = "medium (по умолчанию)"

        answer = f"Уровень рассуждений для моделей семейства GPT-5 - {value}"
        return ResponseMessageItem(text=answer)

    def delete_reasoning(self) -> ResponseMessageItem:
        profile_settings = self.get_profile_gpt_settings()
        profile_settings.gpt_5_settings_reasoning_effort_level = None
        profile_settings.save()
        answer = "Удалил уровень рассуждений для моделей семейства GPT-5"
        return ResponseMessageItem(text=answer)

    def verbosity(self) -> ResponseMessageItem:
        try:
            if self.event.message.args[1] in ["удалить", "сброс", "сбросить", "delete", "reset"]:
                return self.delete_verbosity()
            return self.set_verbosity()
        except:
            return self.get_verbosity()

    def set_verbosity(self) -> ResponseMessageItem:
        user_value = self.event.message.args[1]
        available_levels = [effort_level.value for effort_level in GPTVerbosityLevel]  # noqa
        if user_value not in available_levels:
            available_levels_str = ", ".join(available_levels)
            raise PWarning(f"Уровня {user_value} нет среди доступных.\nДоступные уровни: {available_levels_str}")

        profile_settings = self.get_profile_gpt_settings()
        profile_settings.gpt_5_settings_verbosity_level = user_value
        profile_settings.save()
        answer = f"Установил уровень многословности {user_value} для моделей семейства GPT-5"
        return ResponseMessageItem(text=answer)

    def get_verbosity(self) -> ResponseMessageItem:
        profile_settings = self.get_profile_gpt_settings()
        if profile_settings.gpt_5_settings_verbosity_level:
            value = profile_settings.gpt_5_settings_verbosity_level
        else:
            value = "medium (по умолчанию)"

        answer = f"Уровень многословности для моделей семейства GPT-5 - {value}"
        return ResponseMessageItem(text=answer)

    def delete_verbosity(self) -> ResponseMessageItem:
        profile_settings = self.get_profile_gpt_settings()
        profile_settings.gpt_5_settings_verbosity_level = None
        profile_settings.save()
        answer = "Удалил уровень многословности для моделей семейства GPT-5"
        return ResponseMessageItem(text=answer)
