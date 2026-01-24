from apps.bot.consts import Role
from apps.commands.gpt.commands.gpt.base import GPTCommand
from apps.commands.gpt.commands.gpt.functionality.completions import GPTCompletionsFunctionality
from apps.commands.gpt.commands.gpt.functionality.image_draw import GPTImageDrawFunctionality
from apps.commands.gpt.commands.gpt.functionality.vision import GPTVisionFunctionality
from apps.commands.gpt.commands.gpt.mixins.gpt_5_settings import GPT5SettingsMixin
from apps.commands.gpt.commands.gpt.mixins.key import GPTKeyMixin
from apps.commands.gpt.commands.gpt.mixins.model_choice import GPTModelChoiceMixin
from apps.commands.gpt.commands.gpt.mixins.preprompt import GPTPrepromptMixin
from apps.commands.gpt.commands.gpt.mixins.preset import GPTPresetMixin
from apps.commands.gpt.commands.gpt.mixins.settings import GPTSettingsMixin
from apps.commands.gpt.commands.gpt.mixins.statistics import GPTStatisticsMixin
from apps.commands.gpt.providers.base import GPTProvider
from apps.commands.gpt.providers.providers.chatgpt import ChatGPTProvider
from apps.commands.help_text import HelpTextItem, HelpText


class ChatGPTCommand(
    GPTCommand,
    GPTCompletionsFunctionality,
    GPTVisionFunctionality,
    GPTImageDrawFunctionality,
    GPT5SettingsMixin
):
    name = "gpt"
    names = ["гпт", "chatgpt", "чатгпт"]
    access = Role.TRUSTED
    abstract = False

    provider: GPTProvider = ChatGPTProvider()

    help_text = HelpText(
        commands_text="чат ChatGPT",
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
                GPTModelChoiceMixin.VOICE_RECOGNITION_HELP_TEXT_ITEMS +
                GPTKeyMixin.KEY_HELP_TEXT_ITEMS +
                GPT5SettingsMixin.GPT_5_SETTINGS_HELP_TEXT_ITEMS +
                GPTPresetMixin.PRESET_HELP_TEXT_ITEMS +
                GPTSettingsMixin.SETTINGS_HELP_TEXT_ITEMS
            )
        ],
        help_text_keys=[
            HelpTextItem(
                Role.USER,
                [
                    GPTImageDrawFunctionality.KEY_ITEM_ORIG,
                    GPTImageDrawFunctionality.KEY_ITEM_COUNT,
                    GPTImageDrawFunctionality.KEY_ITEM_HD
                ] +
                GPTImageDrawFunctionality.KEY_ITEMS_FORMAT +
                GPTStatisticsMixin.STATISTICS_KEY_ITEMS_KEY
            )
        ],
        extra_text=f"{GPTCommand.EXTRA_TEXT}\n\n{GPTPrepromptMixin.EXTRA_TEXT}\n\n{GPTImageDrawFunctionality.EXTRA_TEXT}"
    )
