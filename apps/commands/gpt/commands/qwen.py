from apps.bot.consts import RoleEnum
from apps.commands.gpt.commands_utils.gpt.functionality.completions import GPTCompletionsFunctionality
from apps.commands.gpt.commands_utils.gpt.functionality.vision import GPTVisionFunctionality
from apps.commands.gpt.commands_utils.gpt.gpt_abstract import GPTCommand
from apps.commands.gpt.commands_utils.gpt.mixins.preprompt import GPTPrepromptMixin
from apps.commands.gpt.commands_utils.gpt.mixins.preset import GPTPresetMixin
from apps.commands.gpt.commands_utils.gpt.mixins.settings import GPTSettingsMixin
from apps.commands.gpt.commands_utils.gpt.mixins.statistics import GPTStatisticsMixin
from apps.commands.gpt.providers.providers.qwen import QwenProvider
from apps.commands.help_text import HelpTextItem, HelpText


class QwenCommand(
    GPTCommand,
    GPTCompletionsFunctionality,
    GPTVisionFunctionality,
):
    name = "qwen"
    names = ["квен"]
    access = RoleEnum.TRUSTED
    abstract = False

    provider: QwenProvider = QwenProvider()

    help_text = HelpText(
        commands_text="чат Qwen",
        help_texts=[
            HelpTextItem(
                access,
                GPTCompletionsFunctionality.COMPLETIONS_HELP_TEXT_ITEMS +
                GPTVisionFunctionality.VISION_HELP_TEXT_ITEMS +
                GPTPrepromptMixin.PREPROMPT_HELP_TEXT_ITEMS +
                GPTStatisticsMixin.STATISTICS_HELP_TEXT_ITEMS +
                GPTPresetMixin.PRESET_HELP_TEXT_ITEMS +
                GPTSettingsMixin.SETTINGS_HELP_TEXT_ITEMS
            )
        ],
        extra_text=f"{GPTCommand.EXTRA_TEXT}\n\n{GPTPrepromptMixin.EXTRA_TEXT}"
    )
