from apps.bot.classes.const.exceptions import PSkip
from apps.bot.commands.easy.bye import Bye
from apps.bot.commands.easy.clear import Clear
from apps.bot.commands.easy.documentation import Documentation
from apps.bot.commands.easy.donate import Donate
from apps.bot.commands.easy.gay_answer import GayAnswer
from apps.bot.commands.easy.git import Git
from apps.bot.commands.easy.google import Google
from apps.bot.commands.easy.hi import Hi
from apps.bot.commands.easy.issues import Issues
from apps.bot.commands.easy.no import No
from apps.bot.commands.easy.ping import Ping
from apps.bot.commands.easy.sho import Sho
from apps.bot.commands.easy.sorry_me import SorryMe
from apps.bot.commands.easy.start_lada import StartLada
from apps.bot.commands.easy.thanks import Thanks
from apps.bot.commands.easy.yes import Yes
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


class CommandClearTestCase(BotInitializer):
    Command = Clear

    def test_no_args(self):
        return self.check_correct_answer()


class CommandDocumentationTestCase(BotInitializer):
    Command = Documentation

    def test_no_args(self):
        return self.check_correct_answer()


class CommandDonateTestCase(BotInitializer):
    Command = Donate

    def test_no_args(self):
        return self.check_correct_answer()


class CommandGayAnswerTestCase(BotInitializer):
    Command = GayAnswer

    def test_no_args(self):
        return self.check_correct_answer()


class CommandGitTestCase(BotInitializer):
    Command = Git

    def test_no_args(self):
        return self.check_correct_answer()


class CommandGoogleTestCase(BotInitializer):
    Command = Google

    def test_no_args(self):
        self.check_correct_pwarning()

    def test_google_link(self):
        self.event.set_message("гугл привет")
        self.check_correct_answer()


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


class CommandIssuesTestCase(BotInitializer):
    Command = Issues

    def test_no_args(self):
        return self.check_correct_answer()


class CommandNoTestCase(BotInitializer):
    Command = No

    def test_no_args(self):
        return self.check_correct_answer()


class CommandPingTestCase(BotInitializer):
    Command = Ping

    def test_no_args(self):
        return self.check_correct_answer()


class CommandShoTestCase(BotInitializer):
    Command = Sho

    def test_no_args(self):
        return self.check_correct_answer()


class CommandSorryMeTestCase(BotInitializer):
    Command = SorryMe

    def test_no_args(self):
        return self.check_correct_answer()


class CommandStartLadaTestCase(BotInitializer):
    Command = StartLada

    def test_no_args(self):
        return self.check_correct_answer()


class CommandThanksTestCase(BotInitializer):
    Command = Thanks

    def test_no_args(self):
        return self.check_correct_answer()


class CommandYesTestCase(BotInitializer):
    Command = Yes

    def test_no_args(self):
        return self.check_correct_answer()
