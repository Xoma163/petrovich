from apps.bot.classes.consts.Exceptions import PSkip
from apps.bot.commands.EasyCommands.Bye import Bye
from apps.bot.commands.EasyCommands.Clear import Clear
from apps.bot.commands.EasyCommands.Documentation import Documentation
from apps.bot.commands.EasyCommands.Donate import Donate
from apps.bot.commands.EasyCommands.GayAnswer import GayAnswer
from apps.bot.commands.EasyCommands.Git import Git
from apps.bot.commands.EasyCommands.Google import Google
from apps.bot.commands.EasyCommands.Hi import Hi
from apps.bot.commands.EasyCommands.Issues import Issues
from apps.bot.commands.EasyCommands.No import No
from apps.bot.commands.EasyCommands.Nya import Nya
from apps.bot.commands.EasyCommands.Ping import Ping
from apps.bot.commands.EasyCommands.Rofl import Rofl
from apps.bot.commands.EasyCommands.Shit import Shit
from apps.bot.commands.EasyCommands.Sho import Sho
from apps.bot.commands.EasyCommands.SorryMe import SorryMe
from apps.bot.commands.EasyCommands.StartLada import StartLada
from apps.bot.commands.EasyCommands.Thanks import Thanks
from apps.bot.commands.EasyCommands.Yes import Yes
from apps.bot.tests.BotInitializer import BotInitializer


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


class CommandNyaTestCase(BotInitializer):
    Command = Nya

    def test_no_args(self):
        return self.check_correct_answer()


class CommandPingTestCase(BotInitializer):
    Command = Ping

    def test_no_args(self):
        return self.check_correct_answer()


class CommandRoflTestCase(BotInitializer):
    Command = Rofl

    def test_no_args(self):
        return self.check_correct_answer()


class CommandShitTestCase(BotInitializer):
    Command = Shit

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
