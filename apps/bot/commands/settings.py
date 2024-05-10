from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.event.tg_event import TgEvent
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from petrovich.settings import env


class Settings(Command):
    name = "настройки"
    names = ["настройка"]

    help_text = HelpText(
        commands_text="устанавливает настройки пользователя/чата",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand(
                    None,
                    "присылает текущие настройки и права бота в чате"),
                HelpTextItemCommand(
                    "триггериться (вкл/выкл)",
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
                HelpTextItemCommand(
                    "упоминания (вкл/выкл)",
                    "определяет будет ли бот использовать упоминания вас"),
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
            [['триггериться', 'тригериться', 'триггер', 'тригер'], self.menu_no_mention],
            [['мемы', 'мем'], self.menu_memes],
            [['др', 'днюха'], self.menu_bd],
            [['голосовые', 'голос', 'голосовухи', 'голосовуха', 'голосовое'], self.menu_voice],
            [['туретт', 'туррет', 'турретт', 'турет'], self.menu_turett],
            [['ругаться'], self.menu_swear],
            [['упоминание', 'упоминания'], self.menu_use_mention],
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

    def menu_no_mention(self) -> ResponseMessageItem:
        return self.setup_default_chat_setting('no_mention')

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

    def menu_use_mention(self) -> ResponseMessageItem:
        return self.setup_default_profile_setting("use_mention")


    # END PROFILE

    # COMMON

    def menu_bd(self) -> ResponseMessageItem:
        if self.event.is_from_chat:
            return self.setup_default_chat_setting('celebrate_bday')
        else:
            return self.setup_default_profile_setting('celebrate_bday')

    # END COMMON

    def menu_default(self) -> ResponseMessageItem:
        answer = ""
        if self.event.chat:
            answer += self._get_str_chat_settings() + "\n\n"
            if isinstance(self.event, TgEvent):
                answer += self.get_str_chat_tg_settings() + "\n\n"
        answer += self._get_str_user_settings()
        return ResponseMessageItem(text=answer)

    def _get_str_user_settings(self) -> str:
        settings = self.event.sender.settings
        need_meme = settings.need_meme
        need_reaction = settings.need_reaction
        use_swear = settings.use_swear
        celebrate_bday = settings.celebrate_bday
        use_mention = settings.use_mention

        answer = [
            "Настройки пользователя:",
            f"Присылать мемы по точным названиям — {self.TRUE_FALSE_TRANSLATOR[need_meme]}",
            f"Реагировать на неправильные команды — {self.TRUE_FALSE_TRANSLATOR[need_reaction]}",
            f"Использовать ругательные команды — {self.TRUE_FALSE_TRANSLATOR[use_swear]}",
            f"Поздравлять с днём рождения — {self.TRUE_FALSE_TRANSLATOR[celebrate_bday]}",
            f"Использовать упоминания в сообщениях — {self.TRUE_FALSE_TRANSLATOR[use_mention]}",
        ]
        return "\n".join(answer)

    def _get_str_chat_settings(self) -> str:
        settings = self.event.chat.settings
        no_mention = settings.no_mention
        need_turett = settings.need_turett
        recognize_voice = settings.recognize_voice
        celebrate_bday = settings.celebrate_bday

        answer = [
            "Настройки чата:",
            f"Триггериться на команды без упоминания — {self.TRUE_FALSE_TRANSLATOR[no_mention]}",
            f"Синдром Туретта — {self.TRUE_FALSE_TRANSLATOR[need_turett]}",
            f"Автоматически распознавать голосовые — {self.TRUE_FALSE_TRANSLATOR[recognize_voice]}",
            f"Поздравлять с днём рождения — {self.TRUE_FALSE_TRANSLATOR[celebrate_bday]}",
        ]
        return "\n".join(answer)

    def get_str_chat_tg_settings(self) -> str:
        self.bot: TgBot
        chat_admins = self.bot.get_chat_administrators(self.event.chat.chat_id)
        permissions = [x for x in chat_admins if x['user']['id'] == env.int('TG_BOT_GROUP_ID')]
        permissions = permissions[0] if permissions else {}

        can_manage_chat = permissions.get('can_manage_chat', False)
        can_delete_messages = permissions.get('can_delete_messages', False)

        answer = [
            "Права бота в чате:",
            f"Читать все сообщения — {self.TRUE_FALSE_TRANSLATOR[can_manage_chat]}",
            f"Удалять сообщения — {self.TRUE_FALSE_TRANSLATOR[can_delete_messages]}",
        ]
        return "\n".join(answer)

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
