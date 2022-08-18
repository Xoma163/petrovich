from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Exceptions import PWarning
from apps.service.models import Tag as TagModel


class Tag(Command):
    name = "тег"
    names = ["менш", "меншон", "вызов", "клич", "tag", "группа"]
    help_text = "тегает людей в конфе"
    help_texts = [
        "тег создать (название) - добавляет новую группу",
        "тег удалить (название) - удаляет новую группу",
        "тег добавить (название) (имя пользователя/никнейм) - добавляет пользователя в группу",
        "тег убрать (название) (имя пользователя/никнейм) - удаляет пользователя из группы",
        "тег список - выводит список всех тегов",
        "тег (название) - тегает всех пользователей в группе",
    ]
    conversation = True

    def start(self):
        if self.event.message.args:
            arg0 = self.event.message.args[0]
        else:
            arg0 = None

        menu = [
            [["создать", "create"], self.menu_create],
            [['удалить', "delete"], self.menu_delete],
            [["добавить", "add"], self.menu_add],
            [['убрать', "remove"], self.menu_remove],
            [['список', "list"], self.menu_list],
            [['default'], self.menu_default],
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def menu_create(self):
        self.check_args(2)
        name = self.event.message.args[1]
        tag = TagModel.objects.create(name=name, chat=self.event.chat)
        return f"Тег \"{tag.name}\" создан"

    def menu_delete(self):
        self.check_args(2)
        tag = self._get_tag_by_name()
        tag.delete()

    def menu_add(self):
        self.check_args(2)
        tag = self._get_tag_by_name()

        profile_name = self.event.message.args[2]
        profile = self.bot.get_profile_by_name(profile_name, self.event.chat)

        tag.users.add(profile)
        return f"Пользователь {profile} добавлен в тег \"{tag.name}\""

    def menu_remove(self):
        self.check_args(2)
        tag = self._get_tag_by_name()

        profile_name = self.event.message.args[2]
        profile = self.bot.get_profile_by_name(profile_name, self.event.chat)

        tag.users.remove(profile)
        return f"Пользователь {profile} удалён из тега \"{tag.name}\""

    def menu_list(self):
        self.check_args(1)
        tags = TagModel.objects.filter(chat=self.event.chat)
        if not tags:
            return "Тегов нет"

        msg_list = [f"{tag.name} - {', '.join([str(user) for user in tag.users.all()])}" for tag in tags]
        return "\n".join(msg_list)

    def menu_default(self):
        self.check_args(1)
        tag = self._get_tag_by_name(self.event.message.args[0])
        users = tag.users.all()
        if not users:
            raise PWarning("В теге нет пользователей")
        msg_list = [self.bot.get_mention(user) for user in users]
        msg = "\n".join(msg_list)
        return msg

    def _get_tag_by_name(self, tag_name=None):
        if tag_name is None:
            tag_name = self.event.message.args[1]
        try:
            return TagModel.objects.get(name=tag_name, chat=self.event.chat)
        except TagModel.DoesNotExist:
            raise PWarning(f"Тега \"{tag_name}\" не существует")
