from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.service.models import GPTPrePrompt


class Settings(Command):
    name = "настройки"
    names = ["настройка"]

    help_text = HelpText(
        commands_text="устанавливает некоторые настройки пользователя/чата",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand(
                    None,
                    "присылает текущие настройки"),
                HelpTextItemCommand(
                    "упоминание (вкл/выкл)",
                    "определяет будет ли бот триггериться на команды без упоминания в конфе(требуются админские права)"),
                HelpTextItemCommand(
                    "реагировать (вкл/выкл)",
                    "определяет, будет ли бот реагировать на неправильные команды в конфе. Это сделано для того, чтобы в конфе с несколькими ботами не было ложных срабатываний"),
                HelpTextItemCommand(
                    "мемы (вкл/выкл)",
                    "определяет, будет ли бот присылать мем если прислано его точное название без / (боту требуется доступ к переписке)"),
                HelpTextItemCommand(
                    "туретт (вкл/выкл)",
                    "определяет, будет ли бот случайно присылать ругательства"),
                HelpTextItemCommand(
                    "голосовые (вкл/выкл)",
                    "определяет, будет ли бот автоматически распознавать голосовые"),
                HelpTextItemCommand(
                    "др (вкл/выкл)",
                    "определяет, будет ли бот поздравлять с Днём рождения и будет ли ДР отображаться в /профиль"),
                HelpTextItemCommand(
                    "ругаться (вкл/выкл)",
                    "определяет будет ли бот использовать ругательные команды"),
            ])
        ],
        extra_text="Если команда запускается в чате, то общие настройки (поздравления с др) будут указываться для текущего чата"
    )

    ON_OFF_TRANSLATOR = {
        'вкл': True,
        'on': True,
        '1': True,
        'true': True,
        'включить': True,
        'включи': True,
        'вруби': True,
        'подключи': True,
        'истина': True,

        'выкл': False,
        'off': False,
        '0': False,
        'false': False,
        'выключить': False,
        'выключи': False,
        'выруби': False,
        'отключи': False,
        'ложь': False
    }

    TRUE_FALSE_TRANSLATOR = {
        True: 'вкл ✅',
        False: 'выкл ⛔'
    }

    def start(self) -> ResponseMessage:
        if self.event.message.args:
            arg0 = self.event.message.args[0]
        else:
            arg0 = None

        menu = [
            [['реагировать', 'реагируй', 'реагирование'], self.menu_reaction],
            [['упоминание', 'упоминания', 'триггериться', 'тригериться'], self.menu_mentioning],
            [['мемы', 'мем'], self.menu_memes],
            [['др', 'днюха'], self.menu_bd],
            [['голосовые', 'голос', 'голосовухи', 'голосовуха', 'голосовое'], self.menu_voice],
            [['туретт', 'туррет', 'турретт', 'турет'], self.menu_turett],
            [['ругаться'], self.menu_swear],
            [['gpt', 'chatgpt'], self.menu_gpt],
            [['default'], self.menu_default],
        ]
        method = self.handle_menu(menu, arg0)
        rm = ResponseMessage(method())
        return rm

    def get_on_or_off(self, arg):
        if arg in self.ON_OFF_TRANSLATOR:
            return self.ON_OFF_TRANSLATOR[arg]
        else:
            raise PWarning("Не понял, включить или выключить?")

    # CHAT

    def menu_mentioning(self) -> ResponseMessageItem:
        return self.setup_default_chat_setting('mentioning')

    def menu_turett(self) -> ResponseMessageItem:
        return self.setup_default_chat_setting("need_turett")

    def menu_voice(self) -> ResponseMessageItem:
        return self.setup_default_chat_setting('recognize_voice')

    # END CHAT

    # PROFILE

    def menu_memes(self) -> ResponseMessageItem:
        return self.setup_default_profile_setting('need_meme')

    def menu_reaction(self) -> ResponseMessageItem:
        return self.setup_default_profile_setting('need_reaction')

    def menu_swear(self) -> ResponseMessageItem:
        return self.setup_default_profile_setting("use_swear")

    # END PROFILE

    # COMMON

    def menu_bd(self) -> ResponseMessageItem:
        if self.event.is_from_chat:
            return self.setup_default_chat_setting('celebrate_bday')
        else:
            return self.setup_default_profile_setting('celebrate_bday')

    def menu_gpt(self) -> ResponseMessageItem:
        self.check_sender(Role.TRUSTED)
        self.check_args(2)

        if self.event.is_from_chat:
            if self.event.message.args[1] in ["конфа", "чат", "chat"]:
                return self._gpt_common_conference_pm(self.event.chat.settings, "чата", 2)
            return self._gpt_profile_conferece()
        else:
            return self._gpt_common_conference_pm(self.event.sender.settings, "лс", 1)

    def _gpt_common_conference_pm(self, settings, save_for: str, arg_index_slice: int) -> ResponseMessageItem:
        if self.event.message.args[arg_index_slice] in ["сбросить", "удалить", "очистить", "удалить"]:
            preprompt = ""
        else:
            preprompt = " ".join(self.event.message.args_case[arg_index_slice:])

        settings.gpt_preprompt = preprompt
        settings.save()

        if not preprompt:
            answer = f'Очистил GPT preprompt для {save_for}'
        else:
            answer = f'Сохранил GPT preprompt для  {save_for}: "{preprompt}"'
        return ResponseMessageItem(text=answer)

    def _gpt_profile_conferece(self) -> ResponseMessageItem:
        if self.event.message.args[1] in ["сбросить", "удалить", "очистить", "удалить"]:
            preprompt = ""
        else:
            preprompt = " ".join(self.event.message.args_case[1:])

        GPTPrePrompt.objects.update_or_create(
            author=self.event.sender, chat=self.event.chat,
            defaults={"gpt_preprompt": preprompt}
        )

        if not preprompt:
            answer = f'Очистил ваш персональный GPT preprompt для чата'
        else:
            answer = f'Сохранил ваш персональный GPT preprompt для чата: "{preprompt}"'
        return ResponseMessageItem(text=answer)

    # END COMMON

    def menu_default(self) -> ResponseMessageItem:
        answer = ""
        if self.event.chat:
            answer = "Настройки чата:\n"

            settings = self.event.chat.settings
            # chat settings
            mentioning = settings.mentioning
            need_turett = settings.need_turett
            recognize_voice = settings.recognize_voice
            # common settings
            celebrate_bday = settings.celebrate_bday

            answer += f"Триггериться на команды без упоминания - {self.TRUE_FALSE_TRANSLATOR[mentioning]}\n"
            answer += f"Синдром Туретта - {self.TRUE_FALSE_TRANSLATOR[need_turett]}\n"
            answer += f"Автоматически распознавать голосовые - {self.TRUE_FALSE_TRANSLATOR[recognize_voice]}\n"
            answer += f"Поздравлять с днём рождения - {self.TRUE_FALSE_TRANSLATOR[celebrate_bday]}\n"
            answer += "\n"

        answer += "Настройки пользователя:\n"

        settings = self.event.sender.settings
        # user settings
        need_meme = settings.need_meme
        need_reaction = settings.need_reaction
        use_swear = settings.use_swear
        # common settings
        celebrate_bday = settings.celebrate_bday

        answer += f"Присылать мемы по точным названиям - {self.TRUE_FALSE_TRANSLATOR[need_meme]}\n"
        answer += f"Реагировать на неправильные команды - {self.TRUE_FALSE_TRANSLATOR[need_reaction]}\n"
        answer += f"Использовать ругательные команды - {self.TRUE_FALSE_TRANSLATOR[use_swear]}\n"
        answer += f"Поздравлять с днём рождения - {self.TRUE_FALSE_TRANSLATOR[celebrate_bday]}\n"

        return ResponseMessageItem(text=answer)

    def setup_default_chat_setting(self, name) -> ResponseMessageItem:
        self.check_conversation()
        return self._setup_default_settings(name, self.event.chat)

    def setup_default_profile_setting(self, name) -> ResponseMessageItem:
        return self._setup_default_settings(name, self.event.sender)

    def _setup_default_settings(self, name, entity) -> ResponseMessageItem:
        self.check_args(2)
        value = self.get_on_or_off(self.event.message.args[1])
        setattr(entity.settings, name, value)
        entity.settings.save()
        answer = "Сохранил настройку"
        return ResponseMessageItem(text=answer)
