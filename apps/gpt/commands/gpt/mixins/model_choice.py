from django.db.models import QuerySet

from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.gpt.api.base import CompletionsAPIMixin, VisionAPIMixin, ImageDrawAPIMixin, VoiceRecognitionAPIMixin
from apps.gpt.commands.gpt.functionality.completions import GPTCompletionsFunctionality
from apps.gpt.models import CompletionsModel, ProfileGPTSettings, VisionModel, ImageDrawModel, ImageEditModel, \
    VoiceRecognitionModel
from apps.gpt.protocols import GPTCommandProtocol


class GPTModelChoiceMixin(GPTCommandProtocol):
    MODEL_CHOOSE_HELP_TEXT_ITEMS = [
        HelpTextArgument("модели", "выводит список доступных моделей"),
        HelpTextArgument("модель", "выведет текущую модель"),
        HelpTextArgument(
            "модель (название модели)",
            "указывает какую модель использовать для обработки текста (completions)"
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
        Установка модели
        """
        if not isinstance(self, GPTCompletionsFunctionality):
            raise PWarning("Для данного провайдера недоступна смена модели")

        profile_gpt_settings = self.get_profile_gpt_settings()

        # Вывод текущей модели
        if len(self.event.message.args) < 2:
            if profile_gpt_settings.completions_model:
                current_model = profile_gpt_settings.completions_model
                current_model_str = self.bot.get_formatted_text_line(current_model.verbose_name)
                answer = f"Текущая модель - {current_model_str}"
            else:
                default_model = self.get_default_completions_model()
                default_model_str = self.bot.get_formatted_text_line(default_model.verbose_name)
                answer = f"Модель не установлена. Используется модель по умолчанию - {default_model_str}"
            return ResponseMessageItem(answer)

        # Установка новой модели
        new_model_str = self.event.message.args[1]

        try:
            gpt_model = CompletionsModel.objects.filter(provider=self.provider_model).get(name=new_model_str)
        except CompletionsModel.DoesNotExist:
            button = self.bot.get_button('Список моделей', command=self.name, args=['модели'])
            keyboard = self.bot.get_inline_keyboard([button])
            raise PWarning("Не понял какая модель", keyboard=keyboard)

        profile_gpt_settings.completions_model = gpt_model
        profile_gpt_settings.save()
        rmi = ResponseMessageItem(text=f"Поменял модель на {self.bot.get_formatted_text_line(gpt_model.verbose_name)}")
        return rmi

    # UTILS

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
                "генерации изображений (draw)",
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
        if _max_lens is None:
            _max_lens = ()
        models_list = []

        for model in models:
            max_len_model_name = max((len(x.name) for x in models))
            extra = []
            if model.is_default:
                extra.append("по-умолчанию")
            if model == profile_gpt_settings.completions_model:
                extra.append("выбрано")
            extra = ", ".join(extra)

            row = _get_row_method(model, extra, max_len_model_name, *_max_lens, 6, 6)

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
