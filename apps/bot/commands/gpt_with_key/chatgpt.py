from apps.bot.api.gpt.chatgptapi import GPTModels, ChatGPTAPI
from apps.bot.api.gpt.message import ChatGPTMessages, GPTMessageRole
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.bot.classes.messages.attachments.document import DocumentAttachment
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.commands.abstract.gpt_command import GPTCommand
from apps.service.models import GPTPrePrompt


class ChatGPT(GPTCommand):
    name = "gpt"
    names = ["гпт", "chatgpt", "чатгпт"]
    abstract = False

    access = Role.USER

    help_text = HelpText(
        commands_text="чат ChatGPT",
        help_texts=[
            HelpTextItem(
                access,
                GPTCommand.DEFAULT_HELP_TEXT_ITEMS + [
                    GPTCommand.VISION_HELP_TEXT_ITEM,
                    GPTCommand.DRAW_HELP_TEXT_ITEM
                ] +
                GPTCommand.PREPROMPT_HELP_TEXT_ITEMS +
                [
                    HelpTextArgument("стата", "статистика по использованию"),
                    HelpTextArgument("ключ (ключ)", "добавляет персональный API ключ"),
                    HelpTextArgument("ключ удалить", "удаляет персональный API ключ"),
                    HelpTextArgument("модели", "выводит список доступных моделей"),
                    HelpTextArgument("модель", "выведет текущую модель"),
                    HelpTextArgument("модель (название модели)", "указывает какую модель использовать")
                ]
            )
        ],
        help_text_keys=GPTCommand.DEFAULT_KEYS,
        extra_text=GPTCommand.DEFAULT_EXTRA_TEXT
    )

    def __init__(self):
        super().__init__(GPTPrePrompt.CHATGPT, ChatGPTAPI, ChatGPTMessages)

    def start(self) -> ResponseMessage:
        if not self.event.sender.check_role(Role.GPT) and not self.event.sender.settings.chat_gpt_key:
            if self.event.message.args[0] in ["ключ", "key"]:
                return ResponseMessage(self.menu_key())
            else:
                self.check_chat_gpt_key()

        arg0 = self.event.message.args[0] if self.event.message.args else None
        menu = [
            [["нарисуй", "draw"], self.menu_draw_image],
            [["стат", "стата", "статистика", "stat", "stats", "statistics"], self.menu_statistics],
            [["препромпт", "препромт", "промпт", "preprompt", "prepromp", "prompt"], self.menu_preprompt],
            [["ключ", "key"], self.menu_key],
            [["модели", "models"], self.menu_models],
            [["модель", "model"], self.menu_model],
            [["_summary"], self.menu__summary],
            [['default'], self.default]
        ]
        method = self.handle_menu(menu, arg0)
        answer = method()
        return ResponseMessage(answer)

    # DEFAILT MENU

    # MENU
    def menu_statistics(self) -> ResponseMessageItem:
        """
        Просмотр статистики по использованию
        """
        self.check_pm()
        text_answer, statistics_plot_bytes = self._get_stat_for_user(self.event.sender)
        if not text_answer:
            raise PWarning("Ещё не было использований GPT")

        statistics_plot_image = PhotoAttachment()
        statistics_plot_image.parse(statistics_plot_bytes)
        return ResponseMessageItem(text_answer, attachments=[statistics_plot_image])

    def menu_key(self) -> ResponseMessageItem:
        """
        Установка/удаление персонального ключа ChatGPT
        """

        self.check_args(2)
        arg = self.event.message.args_case[1]

        if arg.lower() == "удалить":
            settings = self.event.sender.settings
            settings.chat_gpt_key = ""
            settings.save()
            rmi = ResponseMessageItem(text="Удалил ваш ключ")
        else:
            if self.event.is_from_chat:
                self.bot.delete_messages(self.event.chat.chat_id, self.event.message.id)
                raise PWarning(
                    "Держите свой ключ в секрете. Я удалил ваше сообщение с ключом (или удалите сами если у меня нет прав). Добавьте его в личных сообщениях")
            settings = self.event.sender.settings
            settings.chat_gpt_key = arg
            settings.save()
            rmi = ResponseMessageItem(text="Добавил новый ключ")

        return rmi

    def menu_models(self) -> ResponseMessageItem:
        """
        Просмотр списка моделей
        """

        gpt_models = GPTModels.get_completions_models()
        models_list = [
            f"{self.bot.get_formatted_text_line(x.name)} (${x.prompt_1m_token_cost} / ${x.completion_1m_token_cost})"
            for x in gpt_models
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

        if len(self.event.message.args) < 2:
            settings = self.event.sender.settings
            if settings.chat_gpt_model:
                answer = f"Текущая модель - {self.bot.get_formatted_text_line(settings.get_gpt_model().name)}"
            else:
                default_model = self.bot.get_formatted_text_line(self.gpt_api_class.DEFAULT_COMPLETIONS_MODEL.name)
                answer = f"Модель не установлена. Используется модель по умолчанию - {default_model}"
            return ResponseMessageItem(answer)

        new_model = self.event.message.args[1]
        settings = self.event.sender.settings

        try:
            gpt_model = GPTModels.get_model_by_name(new_model)
        except ValueError:
            button = self.bot.get_button('Список моделей', command=self.name, args=['модели'])
            keyboard = self.bot.get_inline_keyboard([button])
            raise PWarning("Не понял какая модель", keyboard=keyboard)

        settings.chat_gpt_model = gpt_model.name
        settings.save()
        rmi = ResponseMessageItem(text=f"Поменял модель на {self.bot.get_formatted_text_line(settings.chat_gpt_model)}")
        return rmi

    def menu__summary(self):
        PROMPT = "Я пришлю тебе голосовое сообщение. Сделай саммари по нему, сократи и донеси суть, но не теряй важных деталей"
        message = self.event.raw['callback_query']['message']

        documents: list[DocumentAttachment] = self.event.get_all_attachments([DocumentAttachment])
        if documents and documents[0].mime_type.is_text:
            text = documents[0].read_text()
        elif message_text := message.get('text'):
            text = message_text
        # self.get_dialog()
        history = self.gpt_messages_class()

        preprompt = self.get_preprompt(self.event.sender, self.event.chat)
        if preprompt:
            history.add_message(GPTMessageRole.SYSTEM, preprompt)

        history.add_message(GPTMessageRole.USER, PROMPT)
        history.add_message(GPTMessageRole.USER, text)

        rmi = self.completions(history, use_statistics=True)
        return self._send_rmi(rmi)
