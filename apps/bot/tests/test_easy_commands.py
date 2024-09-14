from apps.bot.classes.const.exceptions import PSkip
from apps.bot.commands.easy.bye import Bye
from apps.bot.commands.easy.documentation import Documentation
from apps.bot.commands.easy.donate import Donate
from apps.bot.commands.easy.git import Git
from apps.bot.commands.easy.hi import Hi
from apps.bot.commands.easy.thanks import Thanks
from apps.bot.tests.bot_initializer import BotInitializer


class CommandByeTestCase(BotInitializer):
    Command = Bye

    def test_no_args_pm(self):
        self.event.is_from_pm = True
        return self.check_correct_answer()

    def test_no_args_chat(self):
        self.event.is_from_chat = True
        try:
            return self.check_correct_answer()
        except PSkip:
            return True


class CommandDocumentationTestCase(BotInitializer):
    Command = Documentation

    def test_no_args(self):
        return self.check_correct_answer()


class CommandDonateTestCase(BotInitializer):
    Command = Donate

    def test_no_args(self):
        return self.check_correct_answer()


class CommandGitTestCase(BotInitializer):
    Command = Git

    def test_no_args(self):
        return self.check_correct_answer()


class CommandHiTestCase(BotInitializer):
    Command = Hi

    def test_no_args_pm(self):
        self.event.is_from_pm = True
        return self.check_correct_answer()

    def test_no_args_chat(self):
        self.event.is_from_chat = True
        try:
            return self.check_correct_answer()
        except PSkip:
            return True


class CommandThanksTestCase(BotInitializer):
    Command = Thanks

    def test_no_args_pm(self):
        self.event.is_from_pm = True
        return self.check_correct_answer()

    def test_no_args_chat(self):
        self.event.is_from_chat = True
        try:
            return self.check_correct_answer()
        except PSkip:
            return True
