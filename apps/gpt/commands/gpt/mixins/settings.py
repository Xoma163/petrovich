from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.gpt.commands.gpt.mixins.preprompt import GPTPrepromptMixin
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
            f"Препромпт:\n{self.bot.get_formatted_text(preprompt.text)}" if preprompt else None
        ]

        answer_parts = list(filter(None, answer_parts))
        if len(answer_parts) == 1:
            answer = "Ваши настройки не переопределены"
            return ResponseMessageItem(text=answer)

        answer = "\n\n".join(answer_parts)
        return ResponseMessageItem(text=answer)
