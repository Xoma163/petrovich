from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpTextItem, HelpText
from apps.gpt.commands.gpt.base import GPTCommand
from apps.gpt.commands.gpt.functionality.completions import CompletionsFunctionality
from apps.gpt.commands.gpt.functionality.key import KeyFunctionality
from apps.gpt.commands.gpt.functionality.model_choice import ModelChoiceFunctionality
from apps.gpt.commands.gpt.functionality.preprompt import PrepromptFunctionality
from apps.gpt.commands.gpt.functionality.statistics import StatisticsFunctionality
from apps.gpt.commands.gpt.functionality.vision import VisionFunctionality
from apps.gpt.providers.base import GPTProvider
from apps.gpt.providers.providers.claude import ClaudeProvider


class ClaudeCommand(
    GPTCommand,
    CompletionsFunctionality,
    VisionFunctionality,
    PrepromptFunctionality,
    StatisticsFunctionality,
    ModelChoiceFunctionality,
    KeyFunctionality
):
    name = "claude"
    names = ["клауд"]
    access = Role.GPT
    abstract = False

    provider: GPTProvider = ClaudeProvider()

    help_text = HelpText(
        commands_text="чат Claude",
        help_texts=[
            HelpTextItem(
                access,
                CompletionsFunctionality.COMPLETIONS_HELP_TEXT_ITEMS +
                VisionFunctionality.VISION_HELP_TEXT_ITEMS +
                PrepromptFunctionality.PREPROMPT_HELP_TEXT_ITEMS +
                StatisticsFunctionality.STATISTICS_HELP_TEXT_ITEMS +
                ModelChoiceFunctionality.MODEL_CHOOSE_HELP_TEXT_ITEMS +
                KeyFunctionality.KEY_HELP_TEXT_ITEMS

            )
        ],
        extra_text=f"{GPTCommand.EXTRA_TEXT}\n\n{PrepromptFunctionality.EXTRA_TEXT}"
    )
