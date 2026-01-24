from apps.bot.models import Profile
from apps.commands.gpt.models import Provider, ProfileGPTSettings
from apps.commands.gpt.providers.base import GPTProvider
from apps.shared.exceptions import PWarning


def get_gpt_provider(provider):
    try:
        return Provider.objects.get(name=provider.type_enum.value)
    except Provider.DoesNotExist:
        raise PWarning("Провайдер не определён. Сообщите админу.")


def user_has_api_key(sender: Profile, provider: GPTProvider) -> bool:
    chat_gpt_provider = get_gpt_provider(provider)
    try:
        profile_gpt_settings = sender.gpt_settings.get(provider=chat_gpt_provider)
        return bool(profile_gpt_settings.get_key())
    except ProfileGPTSettings.DoesNotExist:
        return False
