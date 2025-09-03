from typing import Callable

from django.db.models import QuerySet

from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.gpt.api.base import CompletionsAPIMixin, VisionAPIMixin, ImageDrawAPIMixin, VoiceRecognitionAPIMixin
from apps.gpt.models import (
    CompletionsModel,
    ProfileGPTSettings,
    VisionModel,
    ImageDrawModel,
    ImageEditModel,
    VoiceRecognitionModel,
    GPTModel
)
from apps.gpt.protocols import GPTCommandProtocol


class GPTModelChoiceMixin(GPTCommandProtocol):
    MODEL_CHOOSE_HELP_TEXT_ITEMS = [
        HelpTextArgument("модели", "выводит список доступных моделей"),
        HelpTextArgument("модель", "выведет текущие модели")
    ]

    COMPLETIONS_HELP_TEXT_ITEMS = [
        HelpTextArgument(
            "модель completions (название модели)",
            "Указывает какую модель использовать для обработки текста (completions)"
        ),
        HelpTextArgument(
            "модель completions удалить",
            "Удаляет выбранную модель для обработки текста (completions)"
        )
    ]
    VISION_HELP_TEXT_ITEMS = [
        HelpTextArgument(
            "модель vision (название модели)",
            "Указывает какую модель использовать для обработки изображений (vision)"
        ),
        HelpTextArgument(
            "модель vision удалить",
            "Удаляет выбранную модель для обработки изображений (vision)"
        )
    ]
    IMAGE_DRAW_HELP_TEXT_ITEMS = [
        HelpTextArgument(
            "модель draw (название модели)",
            "Указывает какую модель использовать для генерации изображений (draw)"
        ),
        HelpTextArgument(
            "модель draw удалить",
            "Удаляет выбранную модель для генерации изображений (draw)"
        )
    ]
    VOICE_RECOGNITION_HELP_TEXT_ITEMS = [
        HelpTextArgument(
            "модель voice (название модели)",
            "Указывает какую модель использовать для обработки голоса (voice)"
        ),
        HelpTextArgument(
            "модель voice удалить",
            "Удаляет выбранную модель для обработки голоса (voice)"
        )
    ]

    COMPLETIONS_VISION_MODEL_ROW_TEMPLATE = "{model_name} | {input_cost} | {output_cost} | {extra}"
    IMAGE_DRAW_MODEL_ROW_TEMPLATE = "{model_name} | {size} | {quality} | {cost} | {extra}"
    VOICE_RECOGNITION_MODEL_ROW = "{model_name} | {cost} | {extra}"

    # MENU

    def menu_models(self) -> ResponseMessageItem:
        """
        Просмотр списка моделей
        """
        answer = self._get_models_list_of_str()
        answer = "\n\n".join(answer)
        return ResponseMessageItem(answer)

    def menu_model(self) -> ResponseMessageItem:
        """
        Установка модели и просмотр текущей
        """

        profile_gpt_settings = self.get_profile_gpt_settings()

        # Вывод текущих моделей
        if len(self.event.message.args) < 2:
            return self._get_all_current_models(profile_gpt_settings)

        arg = self.event.message.args[1]

        menu = [
            [['completion', 'completions', 'текст', 'текстовая', 'чат'], self._sub_menu_completions_model_choice],
            [["vision", "вижн", 'зрение'], self._sub_menu_vision_model_choice],
            [["draw", "рисования", "рисовать", "изображения"], self._sub_menu_image_draw_model_choice],
            [["voice", "голос", "голосовая"], self._sub_menu_voice_recognition_model_choice],
            [['default'], self._get_all_current_models]
        ]
        method = self.handle_menu(menu, arg)
        rmi = method(profile_gpt_settings)
        return rmi

    # MENU MODEL

    def _get_models_list_of_str(self) -> list:
        profile_gpt_settings = self.get_profile_gpt_settings()
        answer = []
        if issubclass(self.provider.api_class, CompletionsAPIMixin):
            completions_models = CompletionsModel.objects.filter(provider=self.provider_model).order_by('name')
            completions_models_str = self._get_models_str(
                completions_models,
                profile_gpt_settings,
                self._get_completions_vision_row,
                "обработки текста (completions)",
                "Название | цена за 1кк входных токенов | цена за 1кк выходных токенов",
                (6, 6)
            )
            answer.append(completions_models_str)
        if issubclass(self.provider.api_class, VisionAPIMixin):
            vision_models = VisionModel.objects.filter(provider=self.provider_model).order_by('name')
            vision_models_str = self._get_models_str(
                vision_models,
                profile_gpt_settings,
                self._get_completions_vision_row,
                "обработки изображений (vision)",
                "Название | цена за 1кк входных токенов | цена за 1кк выходных токенов",
                (6, 6)
            )
            answer.append(vision_models_str)
        if issubclass(self.provider.api_class, ImageDrawAPIMixin):
            image_draw_models = ImageDrawModel.objects \
                .filter(provider=self.provider_model) \
                .order_by('name', '-width', '-height', '-image_cost')
            image_draw_models_str = self._get_models_str(
                image_draw_models,
                profile_gpt_settings,
                self._get_image_draw_image_edit_row,
                "генерации изображений (draw)",
                "Название | размер | качество | цена за 1шт.",
                (9, 8, 6)
            )
            answer.append(image_draw_models_str)
        if issubclass(self.provider.api_class, VoiceRecognitionAPIMixin):
            voice_recognition_models = VoiceRecognitionModel.objects \
                .filter(provider=self.provider_model) \
                .order_by('name')
            voice_recognition_models_str = self._get_models_str(
                voice_recognition_models,
                profile_gpt_settings,
                self._get_voice_recognition_row,
                "распознавания голоса (voice)",
                "Название | цена за минуту",
                (6,)

            )
            answer.append(voice_recognition_models_str)

        if len(answer) == 0:
            raise PWarning("В базе нет моделей. Сообщите админу")
        return answer

    def _get_models_str(
            self,
            models: QuerySet[CompletionsModel | VisionModel | ImageDrawModel | ImageEditModel],
            profile_gpt_settings: ProfileGPTSettings,
            _get_row_method,
            _models_for_str: str,
            _format: str,
            _max_lens: tuple[int, ...] | None = None,

    ) -> str:
        """
        Универсальный генератор списка моделей

        :models - QuerySet моделей
        :profile_gpt_settings - настройки профиля GPT
        :_get_row_method - метод для получения строки в цикле по моделям
        :_models_for_str - текст для пользователя, который указывает какие это были модели
        :_format - текст для пользователя, в котором указан порядок столбцов
        :_max_lens - tuple, в котором указаны максимальные длины ячеек


        """
        if _max_lens is None:
            _max_lens = ()
        models_list = []

        max_len_model_name = max((len(x.name) for x in models))
        for model in models:
            extra = []
            if model.is_default:
                extra.append("по-умолчанию")
            if model == profile_gpt_settings.completions_model:
                extra.append("выбрано")
            extra = ", ".join(extra)

            # Здесь передаётся модель и экстра текст. В *args максимальная длина имён моделей и _max_lens
            row = _get_row_method(model, extra, max_len_model_name, *_max_lens)

            models_list.append(row)
        models_str = "\n".join(models_list)
        models_str = self.bot.get_formatted_text(models_str)
        return (
            f"Список доступных моделей {_models_for_str}:\n"
            f"{_format}\n"
            f"{models_str}"
        )

    def _get_completions_vision_row(self, model: CompletionsModel | VisionModel, extra_text="", *max_lens):
        input_cost = f"${float(model.prompt_1m_token_cost)}"
        output_cost = f"${float(model.completion_1m_token_cost)}"

        filler_model_name = " " * (max_lens[0] - len(model.name))
        filler_input_cost = " " * (max_lens[1] - len(input_cost))
        fillet_output_cost = " " * (max_lens[2] - len(output_cost))

        return self.COMPLETIONS_VISION_MODEL_ROW_TEMPLATE.format(
            model_name=model.name + filler_model_name,
            input_cost=input_cost + filler_input_cost,
            output_cost=output_cost + fillet_output_cost,
            extra=extra_text
        )

    def _get_image_draw_image_edit_row(self, model: ImageDrawModel | ImageEditModel, extra_text="", *max_lens):
        cost = f"${float(model.image_cost)}"

        filler_model_name = " " * (max_lens[0] - len(model.name))
        filler_size = " " * (max_lens[1] - len(model.size))
        filler_quality = " " * (max_lens[2] - len(model.quality))
        filler_cost = " " * (max_lens[3] - len(cost))

        return self.IMAGE_DRAW_MODEL_ROW_TEMPLATE.format(
            model_name=model.name + filler_model_name,
            size=model.size + filler_size,
            quality=model.quality + filler_quality,
            cost=cost + filler_cost,
            extra=extra_text
        )

    def _get_voice_recognition_row(self, model: VoiceRecognitionModel, extra_text="", *max_lens):
        cost = f"${float(model.voice_recognition_1_min_cost)}"

        filler_model_name = " " * (max_lens[0] - len(model.name))
        filler_cost = " " * (max_lens[1] - len(model.name))

        return self.VOICE_RECOGNITION_MODEL_ROW.format(
            model_name=model.name + filler_model_name,
            cost=cost + filler_cost,
            extra=extra_text
        )

    # MENU MODELS

    def _sub_menu_completions_model_choice(self, profile_gpt_settings: ProfileGPTSettings):
        """
        Подменю выбора конкретной технологии (completions)
        Удаление или изменение модели
        """
        if not issubclass(self.provider.api_class, CompletionsAPIMixin):
            raise PWarning(f"{self.provider.type_enum.value} не умеет обрабатывать текст")
        if len(self.event.message.args) < 3:
            return ResponseMessageItem(text=self._get_current_completions_model_str(profile_gpt_settings))
        new_model_name = self.event.message.args[2]
        if new_model_name in ["удалить", "сброс", "сбросить", "delete", "reset"]:
            profile_gpt_settings.completions_model = None
            profile_gpt_settings.save()
            return ResponseMessageItem(text=f"Удалил модель обработки текста (completions)")

        new_model = self._find_model(CompletionsModel, new_model_name)
        profile_gpt_settings.completions_model = new_model
        profile_gpt_settings.save()
        answer = f"Поменял модель обработки текста (completions) на {self.bot.get_formatted_text_line(new_model.name)}"
        return ResponseMessageItem(text=answer)

    def _sub_menu_vision_model_choice(self, profile_gpt_settings: ProfileGPTSettings):
        if not issubclass(self.provider.api_class, VisionAPIMixin):
            raise PWarning(f"{self.provider.type_enum.value} не умеет обрабатывать изображения")
        if len(self.event.message.args) < 3:
            return ResponseMessageItem(text=self._get_current_vision_model_str(profile_gpt_settings))

        new_model_name = self.event.message.args[2]
        if new_model_name in ["удалить", "сброс", "сбросить", "delete", "reset"]:
            profile_gpt_settings.vision_model = None
            profile_gpt_settings.save()
            return ResponseMessageItem(text=f"Удалил модель обработки изображений (vision)")

        new_model = self._find_model(VisionModel, new_model_name)
        profile_gpt_settings.vision_model = new_model
        profile_gpt_settings.save()
        answer = f"Поменял модель обработки изображений (vision) на {self.bot.get_formatted_text_line(new_model.name)}"
        return ResponseMessageItem(text=answer)

    def _sub_menu_image_draw_model_choice(self, profile_gpt_settings: ProfileGPTSettings):
        if not issubclass(self.provider.api_class, ImageDrawAPIMixin):
            raise PWarning(f"{self.provider.type_enum.value} не умеет генерировать изображения")
        if len(self.event.message.args) < 3:
            return ResponseMessageItem(text=self._get_current_image_draw_model_str(profile_gpt_settings))

        new_model_name = self.event.message.args[2]
        if new_model_name in ["удалить", "сброс", "сбросить", "delete", "reset"]:
            profile_gpt_settings.image_draw_model = None
            profile_gpt_settings.save()
            return ResponseMessageItem(text=f"Удалил модель генерации изображений (draw)")

        new_model_name = self.event.message.args[2]
        try:
            # ToDo: Особенное получение модели, в будущем будет усложнено данными в .filter
            new_model = ImageDrawModel.objects.filter(name=new_model_name).first()
        except ImageDrawModel.DoesNotExist:
            button = self.bot.get_button('Список моделей', command=self.name, args=['модели'])
            keyboard = self.bot.get_inline_keyboard([button])
            raise PWarning("Не понял какая модель", keyboard=keyboard)

        profile_gpt_settings.image_draw_model = new_model
        profile_gpt_settings.save()
        answer = f"Поменял модель генерации изображения (draw) на {self.bot.get_formatted_text_line(new_model.name)}"
        return ResponseMessageItem(text=answer)

    def _sub_menu_voice_recognition_model_choice(self, profile_gpt_settings: ProfileGPTSettings):
        if not issubclass(self.provider.api_class, VoiceRecognitionAPIMixin):
            raise PWarning(f"{self.provider.type_enum.value} не умеет обрабатывать голос")
        if len(self.event.message.args) < 3:
            return ResponseMessageItem(text=self._get_current_voice_recognition_model_str(profile_gpt_settings))

        new_model_name = self.event.message.args[2]
        if new_model_name in ["удалить", "сброс", "сбросить", "delete", "reset"]:
            profile_gpt_settings.voice_recognition_model = None
            profile_gpt_settings.save()
            return ResponseMessageItem(text=f"Удалил модель обработки голоса (voice)")

        new_model = self._find_model(VoiceRecognitionModel, new_model_name)
        profile_gpt_settings.voice_recognition_model = new_model
        profile_gpt_settings.save()
        answer = f"Поменял модель обработки голоса (voice) на {self.bot.get_formatted_text_line(new_model.name)}"
        return ResponseMessageItem(text=answer)

    def _find_model(
            self,
            model_class: type[GPTModel],
            name: str
    ):
        """
        Универсальный поиск модели GPT
        :model_class - подкласс django модели GPTModel
        :name - название модели
        """
        try:
            return model_class.objects.get(provider=self.provider_model, name=name)
        except model_class.DoesNotExist:
            button = self.bot.get_button('Список моделей', command=self.name, args=['модели'])
            keyboard = self.bot.get_inline_keyboard([button])
            raise PWarning("Не понял какая модель", keyboard=keyboard)

    ## CURRENT MODEL WORKS

    def _get_current_model_str(self, settings: ProfileGPTSettings, model_field: str,
                               get_default_model_method: Callable) -> str:
        """
        Получение текущей модели, которая установлена у пользователя или получение стандартной модели
        Используется для любых функциональностей

        :settings - Настройки профиля GPT
        :model_field - Название поля настроек профиля GPT, в котором хранится нужная модель
        :get_default_model_method - Метод для получения стандартной модели
        """
        if current_model := getattr(settings, model_field):
            current_model_str = self.bot.get_formatted_text_line(current_model.name)
            return current_model_str
        else:
            default_model = get_default_model_method()
            default_model_str = self.bot.get_formatted_text_line(default_model.name)
            return f"{default_model_str} (по умолчанию)"

    def _get_current_completions_model_str(self, settings: ProfileGPTSettings):
        current_model_str = self._get_current_model_str(
            settings,
            'completions_model',
            self.get_default_completions_model  # noqa
        )
        return f"Текстовая (completions)\n{current_model_str}"

    def _get_current_vision_model_str(self, settings: ProfileGPTSettings):
        # if not isinstance(self, GPTVisionFunctionality):
        #     raise PWarning("")
        current_model_str = self._get_current_model_str(
            settings,
            'vision_model',
            self.get_default_vision_model  # noqa
        )
        return f"Зрения (vision)\n{current_model_str}"

    def _get_current_image_draw_model_str(self, settings: ProfileGPTSettings):
        current_model_str = self._get_current_model_str(
            settings,
            'image_draw_model',
            self.get_default_image_draw_model  # noqa
        )
        return f"Генерации изображений (draw)\n{current_model_str}"

    def _get_current_voice_recognition_model_str(self, settings: ProfileGPTSettings):
        current_model_str = self._get_current_model_str(
            settings,
            'voice_recognition_model',
            self.get_default_voice_recognition_model  # noqa
        )
        return f"Голосовая (voice)\n{current_model_str}"

    def _get_all_current_models(self, profile_gpt_settings: ProfileGPTSettings) -> ResponseMessageItem:
        """
        Получение всех установленных моделей пользователя
        """
        mixins_methods = [
            (CompletionsAPIMixin, self._get_current_completions_model_str),
            (VisionAPIMixin, self._get_current_vision_model_str),
            (ImageDrawAPIMixin, self._get_current_image_draw_model_str),
            (VoiceRecognitionAPIMixin, self._get_current_voice_recognition_model_str),
        ]
        answer = []
        for api_mixin, method in mixins_methods:
            if issubclass(self.provider.api_class, api_mixin):
                answer.append(method(profile_gpt_settings))

        return ResponseMessageItem(text="\n\n".join(answer))
