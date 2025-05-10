from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.gpt.commands.gpt.functionality.completions import GPTCompletionsFunctionality
from apps.gpt.models import CompletionsModel
from apps.gpt.protocols import GPTCommandProtocol


class GPTModelChoiceMixin(GPTCommandProtocol):
    MODEL_CHOOSE_HELP_TEXT_ITEMS = [
        HelpTextArgument("модели", "выводит список доступных моделей"),
        HelpTextArgument("модель", "выведет текущую модель"),
        HelpTextArgument("модель (название модели)", "указывает какую модель использовать")
    ]

    # MENU

    def menu_models(self) -> ResponseMessageItem:
        """
        Просмотр списка моделей
        """
        if not isinstance(self, GPTCompletionsFunctionality):
            raise PWarning("Для данного провайдера недоступен список моделей")

        completions_models = CompletionsModel.objects.filter(provider=self.provider_model).order_by('name')
        if completions_models.count() == 0:
            raise PWarning("В базе нет моделей. Сообщите админу")

        model_row_template = "{model_name} ${input_cost} / ${output_cost}"

        models_list = [
            model_row_template.format(
                model_name=self.bot.get_formatted_text_line(x.name),
                input_cost=float(x.prompt_1m_token_cost.normalize()),
                output_cost=float(x.completion_1m_token_cost.normalize())
            )
            for x in completions_models
        ]
        models_str = "\n".join(models_list)
        answer = (
            "Список доступных моделей:\n"
            "Название (цена за 1кк входных токенов / цена за 1кк выходных токенов)\n"
            f"{models_str}"
        )
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
