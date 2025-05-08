from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpTextItem, HelpText
from apps.gpt.commands.gpt.base import GPTCommand
from apps.gpt.commands.gpt.functionality.completions import GPTCompletionsFunctionality
from apps.gpt.commands.gpt.functionality.image_draw import GPTImageDrawFunctionality
from apps.gpt.commands.gpt.functionality.vision import GPTVisionFunctionality
from apps.gpt.commands.gpt.mixins.key import GPTKeyMixin
from apps.gpt.commands.gpt.mixins.model_choice import GPTModelChoiceMixin
from apps.gpt.commands.gpt.mixins.preprompt import GPTPrepromptMixin
from apps.gpt.commands.gpt.mixins.statistics import GPTStatisticsMixin
from apps.gpt.providers.base import GPTProvider
from apps.gpt.providers.providers.grok import GrokProvider


class GrokCommand(
    GPTCommand,
    GPTCompletionsFunctionality,
    GPTVisionFunctionality,
    GPTImageDrawFunctionality
):
    name = "grok"
    names = ["грок", "грк", "grk"]
    access = Role.GPT
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
                GPTKeyMixin.KEY_HELP_TEXT_ITEMS

            )
        ],
        help_text_keys=[
            HelpTextItem(
                Role.USER, [
                    GPTImageDrawFunctionality.KEY_ITEM_ORIG,
                    GPTImageDrawFunctionality.KEY_ITEM_COUNT,
                ])
        ],
        extra_text=f"{GPTCommand.EXTRA_TEXT}\n\n{GPTPrepromptMixin.EXTRA_TEXT}"
    )
