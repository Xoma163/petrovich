from apps.bot.consts import RoleEnum
from apps.commands.gpt.commands_utils.gpt.functionality.completions import GPTCompletionsFunctionality
from apps.commands.gpt.commands_utils.gpt.functionality.image_draw import GPTImageDrawFunctionality
from apps.commands.gpt.commands_utils.gpt.functionality.vision import GPTVisionFunctionality
from apps.commands.gpt.commands_utils.gpt.gpt_abstract import GPTCommand
from apps.commands.gpt.commands_utils.gpt.mixins.key import GPTKeyMixin
from apps.commands.gpt.commands_utils.gpt.mixins.model_choice import GPTModelChoiceMixin
from apps.commands.gpt.commands_utils.gpt.mixins.preprompt import GPTPrepromptMixin
from apps.commands.gpt.commands_utils.gpt.mixins.preset import GPTPresetMixin
from apps.commands.gpt.commands_utils.gpt.mixins.settings import GPTSettingsMixin
from apps.commands.gpt.commands_utils.gpt.mixins.statistics import GPTStatisticsMixin
from apps.commands.gpt.providers.base import GPTProvider
from apps.commands.gpt.providers.providers.grok import GrokProvider
from apps.commands.help_text import HelpTextItem, HelpText


class GrokCommand(
    GPTCommand,
    GPTCompletionsFunctionality,
    GPTVisionFunctionality,
    GPTImageDrawFunctionality
):
    name = "grok"
    names = ["грок", "грк", "grk"]
    access = RoleEnum.TRUSTED
    abstract = False

    provider: GPTProvider = GrokProvider()

    help_text = HelpText(
        commands_text="чат Grok",
        help_texts=[
            HelpTextItem(
                access,
                GPTCompletionsFunctionality.COMPLETIONS_HELP_TEXT_ITEMS +
                GPTVisionFunctionality.VISION_HELP_TEXT_ITEMS +
                GPTImageDrawFunctionality.IMAGE_DRAW_HELP_TEXT_ITEMS +
                GPTPrepromptMixin.PREPROMPT_HELP_TEXT_ITEMS +
                GPTStatisticsMixin.STATISTICS_HELP_TEXT_ITEMS +
                GPTModelChoiceMixin.MODEL_CHOOSE_HELP_TEXT_ITEMS +
                GPTModelChoiceMixin.COMPLETIONS_HELP_TEXT_ITEMS +
                GPTModelChoiceMixin.VISION_HELP_TEXT_ITEMS +
                GPTModelChoiceMixin.IMAGE_DRAW_HELP_TEXT_ITEMS +
                GPTKeyMixin.KEY_HELP_TEXT_ITEMS +
                GPTPresetMixin.PRESET_HELP_TEXT_ITEMS +
                GPTSettingsMixin.SETTINGS_HELP_TEXT_ITEMS
            )
        ],
        help_text_keys=[
            HelpTextItem(
                RoleEnum.USER, [
                                   GPTImageDrawFunctionality.KEY_ITEM_ORIG,
                                   GPTImageDrawFunctionality.KEY_ITEM_COUNT,
                               ] + GPTStatisticsMixin.STATISTICS_KEY_ITEMS_KEY
            )
        ],
        extra_text=f"{GPTCommand.EXTRA_TEXT}\n\n{GPTPrepromptMixin.EXTRA_TEXT}\n\n{GPTImageDrawFunctionality.EXTRA_TEXT}"
    )
