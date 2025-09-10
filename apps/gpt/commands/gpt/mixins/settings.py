from apps.bot.classes.const.exceptions import PWarning, PError
from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.gpt.commands.gpt.mixins.preprompt import GPTPrepromptMixin
from apps.gpt.enums import GPTDebug
from apps.gpt.models import Preprompt
from apps.gpt.protocols import GPTCommandProtocol


class GPTSettingsMixin(GPTCommandProtocol):
    SETTINGS_HELP_TEXT_ITEMS = [
        HelpTextArgument(
            "настройки",
            "посмотреть текущие настройки, модели и препромпт"
        ),
        HelpTextArgument(
            "настройки удалить",
            "сбрасывает настройки"
        ),
        HelpTextArgument(
            "debug (on/off)",
            "устанавливает дебаг режим. По умолчанию false"
        ),
        HelpTextArgument(
            "debug удалить",
            "удаляет настройку"
        )
    ]

    # MENU

    def settings(self) -> ResponseMessageItem:
        try:
            self.check_args(2)
            if self.event.message.args[1] in ["удалить", "сброс", "сбросить", "delete", "reset"]:
                return self.delete_settings()
            return self.get_settings()
        except PWarning:
            return self.get_settings()

    def delete_settings(self) -> ResponseMessageItem:
        profile_settings = self.get_profile_gpt_settings()

        profile_settings.completions_model = None
        profile_settings.vision_model = None
        profile_settings.image_draw_model = None
        profile_settings.image_edit_model = None
        profile_settings.voice_recognition_model = None
        profile_settings.gpt_5_settings_reasoning_effort_level = None
        profile_settings.gpt_5_settings_verbosity_level = None
        profile_settings.gpt_5_settings_web_search = None
        profile_settings.use_debug = None
        profile_settings.save()

        if isinstance(self, GPTPrepromptMixin):
            try:
                preprompt = Preprompt.objects.get(author=self.event.sender, chat=None, provider=self.provider_model)
                preprompt.delete()
            except Preprompt.DoesNotExist:
                pass

        answer = "Успешно сбросил все настройки GPT"
        return ResponseMessageItem(text=answer)

    def get_settings(self) -> ResponseMessageItem:
        ps = self.get_profile_gpt_settings()
        preprompt = self.get_preprompt(self.event.sender, None)

        answer_parts = [
            "Текущие настройки:",
            f"Модель обработки текста (completions)\n{self.bot.get_formatted_text_line(ps.completions_model.name)}" if ps.completions_model else None,
            f"Модель обработки изображений (vision)\n{self.bot.get_formatted_text_line(ps.vision_model.name)}" if ps.vision_model else None,
            f"Модель генерации изображений (draw)\n{self.bot.get_formatted_text_line(ps.image_draw_model.name)}" if ps.image_draw_model else None,
            f"Модель редактирования изображений (edit)\n{self.bot.get_formatted_text_line(ps.image_edit_model.name)}" if ps.image_edit_model else None,
            f"Модель обработки голоса (voice)\n{self.bot.get_formatted_text_line(ps.voice_recognition_model.name)}" if ps.voice_recognition_model else None,
            f"Уровень рассуждений для моделей семейства GPT-5\n{self.bot.get_formatted_text_line(ps.gpt_5_settings_reasoning_effort_level)}" if ps.gpt_5_settings_reasoning_effort_level else None,
            f"Уровень многословности для моделей семейства GPT-5\n{self.bot.get_formatted_text_line(ps.gpt_5_settings_verbosity_level)}" if ps.gpt_5_settings_verbosity_level else None,
            f"Поиск в интернете для моделей семейства GPT-5\n{self.bot.get_formatted_text_line('Включено') if ps.gpt_5_settings_web_search is True else self.bot.get_formatted_text_line('Выключено')}" if ps.gpt_5_settings_web_search is not None else None,
            f"Дебаг режим\n{self.bot.get_formatted_text_line('Включено') if ps.use_debug is True else self.bot.get_formatted_text_line('Выключено')}" if ps.use_debug is not None else None,
            f"Препромпт:\n{self.bot.get_formatted_text(preprompt.text)}" if preprompt else None
        ]

        answer_parts = list(filter(None, answer_parts))
        if len(answer_parts) == 1:
            answer = "Ваши настройки не переопределены"
            return ResponseMessageItem(text=answer)

        answer = "\n\n".join(answer_parts)
        return ResponseMessageItem(text=answer)

    def debug(self) -> ResponseMessageItem:
        try:
            if self.event.message.args[1] in ["удалить", "сброс", "сбросить", "delete", "reset"]:
                return self._delete_debug()
            return self._set_debug()
        except IndexError:
            return self._get_debug()

    def _set_debug(self) -> ResponseMessageItem:
        user_value = self.event.message.args[1]
        try:
            debug = GPTDebug[user_value.upper()]
        except KeyError:
            available_levels = ", ".join(self.bot.get_formatted_text_line(x.name.lower()) for x in GPTDebug)
            raise PError(f"Значения {user_value} нет среди доступных.\nДоступные уровни: {available_levels}")

        profile_settings = self.get_profile_gpt_settings()
        profile_settings.use_debug = debug.value
        profile_settings.save()
        answer_value = self.bot.get_formatted_text_line(
            "Включил") if profile_settings.use_debug else self.bot.get_formatted_text_line("Выключил")
        answer = f"{answer_value} дебаг режим"
        return ResponseMessageItem(text=answer)

    def _get_debug(self) -> ResponseMessageItem:
        profile_settings = self.get_profile_gpt_settings()
        if profile_settings.use_debug is True:
            value_str = self.bot.get_formatted_text_line("Включено")
        elif profile_settings.use_debug is False:
            value_str = self.bot.get_formatted_text_line("Выключено")
        else:
            value_str = f"{self.bot.get_formatted_text_line('Выключено')} (по умолчанию)"
        answer = f"Дебаг режим\n{value_str}"
        return ResponseMessageItem(text=answer)

    def _delete_debug(self) -> ResponseMessageItem:
        profile_settings = self.get_profile_gpt_settings()
        profile_settings.use_debug = None
        profile_settings.save()
        answer = "Удалил дебаг режим"
        return ResponseMessageItem(text=answer)
