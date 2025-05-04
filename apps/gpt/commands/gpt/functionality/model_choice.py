from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.gpt.api.base import CompletionsMixin
from apps.gpt.commands.gpt.protocols import HasCommandFields
from apps.gpt.gpt_models.base import GPTCompletionModel
from apps.gpt.models import GPTSettings


class ModelChoiceFunctionality(HasCommandFields):
    MODEL_CHOOSE_HELP_TEXT_ITEMS = [
        HelpTextArgument("модели", "выводит список доступных моделей"),
        HelpTextArgument("модель", "выведет текущую модель"),
        HelpTextArgument("модель (название модели)", "указывает какую модель использовать")
    ]

    def menu_models(self) -> ResponseMessageItem:
        """
        Просмотр списка моделей
        """

        gpt_models = self.provider.models

        completions_models = gpt_models.get_completions_models()
        models_list = [
            f"{self.bot.get_formatted_text_line(x.name)} (${x.prompt_1m_token_cost} / ${x.completion_1m_token_cost})"
            for x in completions_models
        ]
        models_str = "\n".join(models_list)
        answer = (
            "Список доступных моделей:"
            "\n"
            "Название (цена за 1кк входных токенов / цена за 1кк выходных токенов)"
            "\n"
            f"{models_str}"
        )
        return ResponseMessageItem(answer)

    def menu_model(self) -> ResponseMessageItem:
        """
        Установка модели
        """

        gpt_settings = getattr(self.event.sender, "gpt_settings", None)
        if not gpt_settings:
            gpt_settings = GPTSettings(profile=self.event.sender)

        settings_model_field = self.provider.gpt_settings_model_field

        if len(self.event.message.args) < 2:
            gpt_model_str = getattr(gpt_settings, settings_model_field)
            if gpt_model_str:
                gpt_model = self.provider.models.get_model_by_name(gpt_model_str, GPTCompletionModel)
                answer = f"Текущая модель - {self.bot.get_formatted_text_line(gpt_model.verbose_name)}"
            else:
                if isinstance(self.provider.api_class, CompletionsMixin):
                    default_model = self.bot.get_formatted_text_line(
                        self.provider.api_class.default_completions_model.name)
                    answer = f"Модель не установлена. Используется модель по умолчанию - {default_model}"
                else:
                    raise PWarning("Для данного GPT отсутствует completions функция")
            return ResponseMessageItem(answer)

        new_model_str = self.event.message.args[1]

        gpt_models = self.provider.models

        try:
            gpt_model = gpt_models.get_model_by_name(new_model_str, GPTCompletionModel)
        except ValueError:
            button = self.bot.get_button('Список моделей', command=self.name, args=['модели'])
            keyboard = self.bot.get_inline_keyboard([button])
            raise PWarning("Не понял какая модель", keyboard=keyboard)

        setattr(gpt_settings, settings_model_field, gpt_model.name)
        gpt_settings.save()
        rmi = ResponseMessageItem(text=f"Поменял модель на {self.bot.get_formatted_text_line(gpt_model.verbose_name)}")
        return rmi
