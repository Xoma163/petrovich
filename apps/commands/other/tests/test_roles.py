from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from apps.bot.consts import RoleEnum
from apps.commands.other.commands.moderator.roles import Roles
from apps.shared.exceptions import PWarning


class RolesTests(SimpleTestCase):
    def test_moderator_can_list_manageable_roles(self):
        command = Roles()
        command.event = SimpleNamespace(
            message=SimpleNamespace(args=["список"], args_str="список"),
            sender=Mock(),
        )
        command.event.sender.check_role.return_value = False

        response = command.start()

        self.assertEqual(
            response.messages[0].text,
            "Доступные для добавления и удаления роли:\n- майнкрафт\n- доверенный",
        )

    def test_admin_can_manage_moderator_role(self):
        command = Roles()
        command.event = SimpleNamespace(sender=Mock())
        command.event.sender.check_role.return_value = True

        self.assertEqual(
            command.get_manageable_roles(),
            [RoleEnum.MODERATOR, RoleEnum.MINECRAFT, RoleEnum.TRUSTED],
        )

    def test_remove_role_rejects_role_missing_from_profile(self):
        profile = Mock()
        profile.check_role.return_value = False

        with self.assertRaisesMessage(PWarning, "У пользователя нет роли"):
            Roles.remove_role(profile, RoleEnum.TRUSTED)

        profile.remove_role.assert_not_called()

    def test_remove_role_removes_existing_role(self):
        profile = Mock()
        profile.check_role.return_value = True

        Roles.remove_role(profile, RoleEnum.TRUSTED)

        profile.remove_role.assert_called_once_with(RoleEnum.TRUSTED)

    @patch("apps.commands.other.commands.moderator.roles.Roles.add_role")
    @patch("apps.commands.other.commands.moderator.roles.get_profile_by_tg_id")
    def test_finds_role_target_by_telegram_id(self, get_profile_by_tg_id, add_role):
        profile = Mock()
        get_profile_by_tg_id.return_value = profile
        command = Roles()
        command.event = SimpleNamespace(
            message=SimpleNamespace(
                args=["добавить", "123456", "доверенный"],
                args_str="добавить 123456 доверенный",
            ),
            sender=Mock(),
            chat=Mock(),
        )
        command.event.sender.check_role.return_value = False

        command.start()

        get_profile_by_tg_id.assert_called_once_with("123456", command.event.chat)
        add_role.assert_called_once_with(profile, RoleEnum.TRUSTED)
