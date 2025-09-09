from apps.bot.classes.const.exceptions import PError
from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.gpt.enums import GPTReasoningEffortLevel, GPTVerbosityLevel, GPTWebSearch
from apps.gpt.protocols import GPTCommandProtocol


class GPT5SettingsMixin(GPTCommandProtocol):
    GPT_5_SETTINGS_HELP_TEXT_ITEMS = [
        HelpTextArgument(
            "gpt_5_reasoning (high/medium/low/minimal)",
            "устанавливает уровень рассуждений для моделей семейства GPT-5. По умолчанию medium"
        ),
        HelpTextArgument(
            "gpt_5_reasoning удалить",
            "удаляет настройку"
        ),
        HelpTextArgument(
            "gpt_5_verbosity (high/medium/low)",
            "устанавливает уровень многословности для моделей семейства GPT-5. По умолчанию medium"
        ),
        HelpTextArgument(
            "gpt_5_verbosity удалить",
            "удаляет настройку"
        ),
        HelpTextArgument(
            "gpt_5_web_search (on/off)",
            "устанавливает возможность поиска информации в интернете для моделей семейства GPT-5. По умолчанию false"
        ),
        HelpTextArgument(
            "gpt_5_web_search удалить",
            "удаляет настройку"
        )
    ]

    def reasoning(self) -> ResponseMessageItem:
        try:
            self.check_args(2)
            if self.event.message.args[1] in ["удалить", "сброс", "сбросить", "delete", "reset"]:
                return self._delete_reasoning()
            return self._set_reasoning()
        except IndexError:
            return self._get_reasoning()

    def _set_reasoning(self) -> ResponseMessageItem:
        user_value = self.event.message.args[1]
        try:
            effort_level = GPTReasoningEffortLevel[user_value.upper()]
        except KeyError:
            available_levels = ", ".join(
                self.bot.get_formatted_text_line(x.name.lower()) for x in GPTReasoningEffortLevel)
            raise PError(f"Уровня {user_value} нет среди доступных.\nДоступные уровни: {available_levels}")

        profile_settings = self.get_profile_gpt_settings()
        profile_settings.gpt_5_settings_reasoning_effort_level = effort_level.value
        profile_settings.save()
        answer = f"Установил уровень рассуждений {self.bot.get_formatted_text_line(user_value)} для моделей семейства GPT-5"
        return ResponseMessageItem(text=answer)

    def _get_reasoning(self) -> ResponseMessageItem:
        profile_settings = self.get_profile_gpt_settings()
        if profile_settings.gpt_5_settings_reasoning_effort_level:
            value_str = self.bot.get_formatted_text_line(profile_settings.gpt_5_settings_reasoning_effort_level)
        else:
            value_str = f"{self.bot.get_formatted_text_line('medium')} (по умолчанию)"

        answer = f"Уровень рассуждений для моделей семейства GPT-5\n{value_str}"
        return ResponseMessageItem(text=answer)

    def _delete_reasoning(self) -> ResponseMessageItem:
        profile_settings = self.get_profile_gpt_settings()
        profile_settings.gpt_5_settings_reasoning_effort_level = None
        profile_settings.save()
        answer = "Удалил уровень рассуждений для моделей семейства GPT-5"
        return ResponseMessageItem(text=answer)

    def verbosity(self) -> ResponseMessageItem:
        try:
            if self.event.message.args[1] in ["удалить", "сброс", "сбросить", "delete", "reset"]:
                return self._delete_verbosity()
            return self._set_verbosity()
        except IndexError:
            return self._get_verbosity()

    def _set_verbosity(self) -> ResponseMessageItem:
        user_value = self.event.message.args[1]
        try:
            verbosity_level = GPTVerbosityLevel[user_value.upper()]
        except KeyError:
            available_levels = ", ".join(self.bot.get_formatted_text_line(x.name.lower()) for x in GPTVerbosityLevel)
            raise PError(f"Уровня {user_value} нет среди доступных.\nДоступные уровни: {available_levels}")

        profile_settings = self.get_profile_gpt_settings()
        profile_settings.gpt_5_settings_verbosity_level = verbosity_level.value
        profile_settings.save()
        answer = f"Установил уровень многословности {self.bot.get_formatted_text_line(user_value)} для моделей семейства GPT-5"
        return ResponseMessageItem(text=answer)

    def _get_verbosity(self) -> ResponseMessageItem:
        profile_settings = self.get_profile_gpt_settings()
        if profile_settings.gpt_5_settings_verbosity_level:
            value_str = self.bot.get_formatted_text_line(profile_settings.gpt_5_settings_verbosity_level)
        else:
            value_str = f"{self.bot.get_formatted_text_line('medium')} (по умолчанию)"

        answer = f"Уровень многословности для моделей семейства GPT-5\n{value_str}"
        return ResponseMessageItem(text=answer)

    def _delete_verbosity(self) -> ResponseMessageItem:
        profile_settings = self.get_profile_gpt_settings()
        profile_settings.gpt_5_settings_verbosity_level = None
        profile_settings.save()
        answer = "Удалил уровень многословности для моделей семейства GPT-5"
        return ResponseMessageItem(text=answer)

    def web_search(self) -> ResponseMessageItem:
        try:
            if self.event.message.args[1] in ["удалить", "сброс", "сбросить", "delete", "reset"]:
                return self._delete_web_search()
            return self._set_web_search()
        except IndexError:
            return self._get_web_search()

    def _set_web_search(self) -> ResponseMessageItem:
        user_value = self.event.message.args[1]
        try:
            web_search = GPTWebSearch[user_value.upper()]
        except KeyError:
            available_levels = ", ".join(self.bot.get_formatted_text_line(x.name.lower()) for x in GPTWebSearch)
            raise PError(f"Значения {user_value} нет среди доступных.\nДоступные уровни: {available_levels}")

        profile_settings = self.get_profile_gpt_settings()
        profile_settings.gpt_5_settings_web_search = web_search.value
        profile_settings.save()
        answer_value = self.bot.get_formatted_text_line(
            "Включил") if profile_settings.gpt_5_settings_web_search else self.bot.get_formatted_text_line("Выключил")
        answer = f"{answer_value} поиск в интернете для моделей семейства GPT-5"
        return ResponseMessageItem(text=answer)

    def _get_web_search(self) -> ResponseMessageItem:
        profile_settings = self.get_profile_gpt_settings()
        if profile_settings.gpt_5_settings_web_search is True:
            value_str = self.bot.get_formatted_text_line("Включено")
        elif profile_settings.gpt_5_settings_web_search is False:
            value_str = self.bot.get_formatted_text_line("Выключено")
        else:
            value_str = f"{self.bot.get_formatted_text_line("Выключено")} (по умолчанию)"
        answer = f"Поиск в интернете для моделей семейства GPT-5\n{value_str}"
        return ResponseMessageItem(text=answer)

    def _delete_web_search(self) -> ResponseMessageItem:
        profile_settings = self.get_profile_gpt_settings()
        profile_settings.gpt_5_settings_web_search = None
        profile_settings.save()
        answer = "Удалил поиск в интернете для моделей семейства GPT-5"
        return ResponseMessageItem(text=answer)
