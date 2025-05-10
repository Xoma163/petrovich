from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.models import Profile
from apps.gpt.models import Provider, ProfileGPTSettings
from apps.gpt.providers.base import GPTProvider


def user_has_role_or_has_gpt_key(sender: Profile, provider: GPTProvider) -> bool:
    try:
        chat_gpt_provider = Provider.objects.get(name=provider.type_enum.value)
    except Provider.DoesNotExist:
        raise PWarning("Провайдер не определён. Сообщите админу.")

    user_has_role_gpt = sender.check_role(Role.GPT)
    if user_has_role_gpt:
        return True

    try:
        profile_gpt_settings = sender.gpt_settings.get(provider=chat_gpt_provider)
        user_has_personal_key = bool(profile_gpt_settings.get_key())
    except ProfileGPTSettings.DoesNotExist:
        user_has_personal_key = False
    if user_has_personal_key:
        return True
    return False
