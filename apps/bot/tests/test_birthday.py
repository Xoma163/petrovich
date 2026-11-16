from datetime import datetime
from unittest.mock import patch

from django.test import TestCase

from apps.bot.consts import PlatformEnum, RoleEnum
from apps.bot.models import Chat, Profile, Role, User
from apps.shared.management.commands.check_birthday import Command


class BirthdayCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Role.objects.get_or_create(name=RoleEnum.USER.name)
        cls.first = Profile.objects.create(name="First", birthday=datetime.now().date())
        cls.second = Profile.objects.create(name="Second", birthday=datetime.now().date())
        User.objects.create(profile=cls.first, platform=PlatformEnum.TG.name, user_id="101")
        User.objects.create(profile=cls.second, platform=PlatformEnum.TG.name, user_id="102")
        cls.first_chat = Chat.objects.create(platform=PlatformEnum.TG.name, chat_id="201")
        cls.second_chat = Chat.objects.create(platform=PlatformEnum.TG.name, chat_id="202")
        cls.disabled_chat = Chat.objects.create(platform=PlatformEnum.TG.name, chat_id="203")
        for chat in (cls.first_chat, cls.second_chat):
            chat.settings.celebrate_bday = True
            chat.settings.save()
        cls.first.chats.add(cls.first_chat, cls.disabled_chat)
        cls.second.chats.add(cls.second_chat, cls.disabled_chat)

    @patch("apps.shared.management.commands.check_birthday.tg_bot")
    def test_each_birthday_uses_its_own_chats_and_prefetched_settings(self, bot):
        bot.get_mention.side_effect = lambda profile: profile.name

        # One profiles query, one chats prefetch, and one Telegram user lookup per profile.
        with self.assertNumQueries(4):
            Command().handle()

        messages = [call.args[0].messages[0] for call in bot.send_response_message.call_args_list]
        self.assertEqual(
            [(message.peer_id, message.text) for message in messages],
            [
                ("101", "С Днём рождения, First!"),
                ("201", "С Днём рождения, First!"),
                ("102", "С Днём рождения, Second!"),
                ("202", "С Днём рождения, Second!"),
            ],
        )

    @patch("apps.shared.management.commands.check_birthday.tg_bot")
    def test_profile_can_disable_birthday_messages(self, bot):
        self.first.settings.celebrate_bday = False
        self.first.settings.save()
        bot.get_mention.side_effect = lambda profile: profile.name

        Command().handle()

        peers = [call.args[0].messages[0].peer_id for call in bot.send_response_message.call_args_list]
        self.assertEqual(peers, ["102", "202"])
