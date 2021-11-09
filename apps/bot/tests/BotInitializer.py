from django.contrib.auth.models import Group
from django.test import TestCase

from apps.bot.classes.Command import Command
from apps.bot.classes.bots.TgBot import TgBot
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning, PError
from apps.bot.classes.events.TgEvent import TgEvent
from apps.bot.models import User, Profile, Chat
from apps.service.management.commands.initial import Command as InitCommand
from apps.service.models import City, TimeZone


class BotInitializer(TestCase):
    Command = Command

    @classmethod
    def setUpTestData(cls):
        initial_command = InitCommand()
        initial_command.init_groups()
        tz, _ = TimeZone.objects.get_or_create(name='Europe/Samara')
        city = {'name': 'Самара', 'synonyms': 'самара смр', 'lat': 53.195538, 'lon': 50.101783, 'timezone': tz}
        city, _ = City.objects.update_or_create(name=city['name'], defaults=city)

        all_groups = Group.objects.exclude(name="BANNED")
        # Первый акк админа
        profile = Profile.objects.create(
            name="Вася",
            surname="Пупкин",
            nickname_real="Васёк",
            gender='2',
            city=city,
        )
        profile.groups.set(all_groups)
        chat = Chat.objects.create(
            name="Чат Васька",
            chat_id=2,
            admin=profile
        )
        profile.chats.add(chat)
        User.objects.create(
            user_id=1,
            profile=profile,
            platform=Platform.TG.name
        )
        # Второй обычный юзер
        profile2 = Profile.objects.create(
            name="Иван",
            surname="Иванов",
            nickname_real="Ванёк",
            gender='2',
            city=city,
        )
        group_user = Group.objects.get(name="USER")
        profile2.groups.add(group_user)
        profile2.chats.add(chat)

        User.objects.create(
            user_id=2,
            profile=profile2,
            platform=Platform.TG.name
        )

    def setUp(self):
        self.bot = TgBot()
        self.event = TgEvent(bot=self.bot)
        self.cmd = self.Command(self.bot, self.event)
        self.setup_event()

    # def tearDown(self):
    #     self.event.message = None

    def setup_event(self):
        self.event.is_from_user = True
        self.event.user = User.objects.get(user_id=1)
        self.event.sender = self.event.user.profile
        self.event.set_message(self.cmd.name)

    def check_correct_answer(self):
        return self.cmd.check_and_start(self.bot, self.event)

    def check_correct_pwarning(self):
        try:
            self.cmd.check_and_start(self.bot, self.event)
        except PWarning:
            return
        self.fail("Команда вернула не PWarning")

    def check_correct_perror(self):
        try:
            self.cmd.check_and_start(self.bot, self.event)
        except PError:
            return
        self.fail("Команда вернула не PError")
