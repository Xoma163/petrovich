from django.db.models import QuerySet

from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.gpt.commands.gpt.mixins.preprompt import GPTPrepromptMixin
from apps.gpt.models import GPTPreset, Preprompt
from apps.gpt.protocols import GPTCommandProtocol


class GPTPresetMixin(GPTCommandProtocol):
    PRESET_HELP_TEXT_ITEMS = [
        HelpTextArgument(
            "пресет создать (название)\\n[описание]",
            "создаёт новый пресет на основе текущих настроек GPT"
        ),
        HelpTextArgument(
            "пресет удалить (название)",
            "удаляет пресет"
        ),
        HelpTextArgument(
            "пресет (название)",
            "выбирает пресет"
        ),
        HelpTextArgument(
            "пресет",
            "показывает все ваши пресеты"
        )
    ]

    # MENU

    def preset(self):
        try:
            self.check_args(2)
            arg1 = self.event.message.args[1]
        except PWarning:
            arg1 = None

        menu = [
            [["добавить", "создать", "сохранить", "add", "save", "create"], self.menu_add_preset],
            [["удалить", "сброс", "сбросить", "delete", "reset"], self.menu_delete_preset],
            [["default"], self.menu_select_or_list_preset],
        ]

        method = self.handle_menu(menu, arg1)
        return method()

    def menu_add_preset(self) -> ResponseMessageItem:
        self.check_args(3)
        name_and_description = self.event.message.clear_case.split(' ', 3)[3]
        parts = name_and_description.split('\n', 1)
        name = parts[0]
        description = parts[1] if len(parts) > 1 else ""

        profile_settings = self.get_profile_gpt_settings()

        preprompt_text = None
        if isinstance(self, GPTPrepromptMixin):
            preprompt = self.get_preprompt(self.event.sender, None)
            if preprompt:
                preprompt_text = preprompt.text

        defaults = {
            "description": description,
            "completions_model": profile_settings.completions_model,
            "vision_model": profile_settings.vision_model,
            "image_draw_model": profile_settings.image_draw_model,
            "image_edit_model": profile_settings.image_edit_model,
            "voice_recognition_model": profile_settings.voice_recognition_model,
            "gpt_5_settings_reasoning_effort_level": profile_settings.gpt_5_settings_reasoning_effort_level,
            "gpt_5_settings_verbosity_level": profile_settings.gpt_5_settings_verbosity_level,
            "gpt_5_settings_web_search": profile_settings.gpt_5_settings_web_search,
            "preprompt_text": preprompt_text,
        }

        try:
            created = False
            preset = GPTPreset.objects.get(
                provider=self.provider_model,
                profile=self.event.sender,
                name=name
            )

            if not description:
                defaults.pop('description')
            for key, value in defaults.items():
                setattr(preset, key, value)
            preset.save()
        except GPTPreset.DoesNotExist:
            created = True
            preset = GPTPreset(
                provider=self.provider_model,
                profile=self.event.sender,
                name=name,
                **defaults
            )
            preset.save()

        answer_parts = [
            f"Сохранил пресет {self.bot.get_formatted_text_line(name)}:" if created else f"Обновилл пресет {self.bot.get_formatted_text_line(name)}:",
            f"Описание\n{self.bot.get_formatted_text_line(preset.description)}" if preset.description else None,
            f"Модель обработки текста (completions)\n{self.bot.get_formatted_text_line(preset.completions_model.name)}" if preset.completions_model else None,
            f"Модель обработки изображений (vision)\n{self.bot.get_formatted_text_line(preset.vision_model.name)}" if preset.vision_model else None,
            f"Модель генерации изображений (draw)\n{self.bot.get_formatted_text_line(preset.image_draw_model.name)}" if preset.image_draw_model else None,
            f"Модель редактирования изображений (edit)\n{self.bot.get_formatted_text_line(preset.image_edit_model.name)}" if preset.image_edit_model else None,
            f"Модель обработки голоса (voice)\n{self.bot.get_formatted_text_line(preset.voice_recognition_model.name)}" if preset.voice_recognition_model else None,
            f"Уровень рассуждений для моделей семейства GPT-5\n{self.bot.get_formatted_text_line(preset.gpt_5_settings_reasoning_effort_level)}" if preset.gpt_5_settings_reasoning_effort_level else None,
            f"Уровень многословности для моделей семейства GPT-5\n{self.bot.get_formatted_text_line(preset.gpt_5_settings_verbosity_level)}" if preset.gpt_5_settings_verbosity_level else None,
            f"Поиск в интернете для моделей семейства GPT-5\n{self.bot.get_formatted_text_line('Включено') if preset.gpt_5_settings_web_search is True else self.bot.get_formatted_text_line('Выключено')}" if preset.gpt_5_settings_web_search is not None else None,
            f"Препромпт:\n{self.bot.get_formatted_text(preset.preprompt_text)}" if preprompt_text else None
        ]

        preset.save()
        answer = "\n\n".join(filter(None, answer_parts))
        return ResponseMessageItem(text=answer)

    def menu_delete_preset(self) -> ResponseMessageItem:
        self.check_args(3)
        name = " ".join(self.event.message.args_case[2:])

        user_presets = self._get_user_presets()
        presets_to_delete = self._get_user_presets_by_name(name)
        if len(presets_to_delete) == 0:
            available_presets_names_str = self._format_presets_str(user_presets)
            raise PWarning(
                f"Не нашёл пресетов по имени \"{name}\" для удаления.\n"
                f"Доступные варианты:\n\n"
                f"{available_presets_names_str}"
            )
        elif len(presets_to_delete) == 1:
            answer = f"Удалил пресет \"{presets_to_delete.first().name}\""
            presets_to_delete.delete()
        else:
            presets_to_delete_names_str = "\n".join([x.name for x in presets_to_delete])
            answer = f"Удалил пресеты:\n" \
                     f"{presets_to_delete_names_str}"
            presets_to_delete.delete()
        return ResponseMessageItem(text=answer)

    def menu_select_preset(self) -> ResponseMessageItem:
        self.check_args(2)
        name = " ".join(self.event.message.args_case[1:])
        available_presets = self._get_user_presets_by_name(name)
        if len(available_presets) == 0:
            raise PWarning("У вас нет сохранённых пресетов")
        if len(available_presets) > 1:
            raise PWarning("Больше двух пресетов подходят на выбор. Уточните выбор или удалите дубликат")

        preset = available_presets.first()
        profile_settings = self.get_profile_gpt_settings()
        profile_settings.completions_model = preset.completions_model if preset.completions_model else None
        profile_settings.vision_model = preset.vision_model if preset.vision_model else None
        profile_settings.image_draw_model = preset.image_draw_model if preset.image_draw_model else None
        profile_settings.image_edit_model = preset.image_edit_model if preset.image_edit_model else None
        profile_settings.voice_recognition_model = preset.voice_recognition_model if preset.voice_recognition_model else None
        profile_settings.gpt_5_settings_reasoning_effort_level = preset.gpt_5_settings_reasoning_effort_level if preset.gpt_5_settings_reasoning_effort_level else None
        profile_settings.gpt_5_settings_verbosity_level = preset.gpt_5_settings_verbosity_level if preset.gpt_5_settings_verbosity_level else None
        profile_settings.gpt_5_settings_web_search = preset.gpt_5_settings_web_search if preset.gpt_5_settings_web_search else None
        profile_settings.save()

        if isinstance(self, GPTPrepromptMixin):
            preprompt = self.get_preprompt(self.event.sender, None)
            if preprompt:
                if preset.preprompt_text:
                    preprompt.text = preset.preprompt_text
                    preprompt.save()
                else:
                    preprompt.delete()
            else:
                if preset.preprompt_text:
                    new_preprompt = Preprompt(
                        provider=self.provider_model,
                        author=self.event.sender,
                        text=preset.preprompt_text
                    )
                    new_preprompt.save()

        answer = f"Загрузил пресет \"{preset.name}\""
        return ResponseMessageItem(text=answer)

    def menu_select_or_list_preset(self) -> ResponseMessageItem:
        try:
            self.check_args(2)
            return self.menu_select_preset()
        except PWarning:
            return self.menu_list_preset()

    def menu_list_preset(self) -> ResponseMessageItem:
        presets = self._get_user_presets()
        if len(presets) == 0:
            raise PWarning("У вас нет сохранённых пресетов")

        presets_names = self._format_presets_str(presets)
        answer = "Сохранённые пресеты:\n\n" \
                 f"{presets_names}"

        buttons = []
        for preset in presets:
            button = self.bot.get_button(preset.name, f"{self.name} пресет {preset.name}")
            buttons.append(button)
        keyboard = self.bot.get_inline_keyboard(buttons, cols=2)
        return ResponseMessageItem(text=answer, keyboard=keyboard)

    def _format_presets_str(self, presets: QuerySet[GPTPreset]) -> str:
        presets_names = []
        for preset in presets:
            row = [self.bot.get_formatted_text_line(preset.name)]
            if preset.description:
                row.append(preset.description)
            row = "\n".join(row)
            presets_names.append(row)
        return "\n\n".join(presets_names)

    # UTILS

    def _get_user_presets(self) -> QuerySet[GPTPreset]:
        return GPTPreset.objects.filter(provider=self.provider_model, profile=self.event.sender)

    def _get_user_presets_by_name(self, name: str) -> QuerySet[GPTPreset]:
        user_presets = self._get_user_presets()
        return user_presets.filter(name__iexact=name)
