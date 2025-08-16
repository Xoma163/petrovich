from apps.bot.classes.const.exceptions import PWarning
from apps.bot.models import Profile
from apps.gpt.models import Provider, ProfileGPTSettings
from apps.gpt.providers.base import GPTProvider


def user_has_api_key(sender: Profile, provider: GPTProvider) -> bool:
    try:
        chat_gpt_provider = Provider.objects.get(name=provider.type_enum.value)
    except Provider.DoesNotExist:
        raise PWarning("Провайдер не определён. Сообщите админу.")

    try:
        profile_gpt_settings = sender.gpt_settings.get(provider=chat_gpt_provider)
        return bool(profile_gpt_settings.get_key())
    except ProfileGPTSettings.DoesNotExist:
        return False
