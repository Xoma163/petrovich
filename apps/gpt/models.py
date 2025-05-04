from django.db import models

from apps.bot.models import Profile, Chat
from apps.gpt.enums import GPTProviderEnum
from apps.gpt.providers.base import GPTProvider
from apps.gpt.usage import GPTUsage as GPTAPIUsage
from apps.service.mixins import TimeStampModelMixin


# Create your models here.

class ProviderModelMixin(models.Model):
    CHATGPT = 'chatgpt'
    CLAUDE = 'claude'
    GROK = 'grok'
    PROVIDER_CHOICES = (
        (CHATGPT, 'СhatGPT'),
        (CLAUDE, 'Claude'),
        (GROK, 'Grok'),
    )

    provider = models.CharField(
        'Провайдер',
        max_length=10,
        choices=[(provider.value, provider.name) for provider in GPTProviderEnum],  # noqa
    )

    class Meta:
        abstract = True


class Preprompt(TimeStampModelMixin, ProviderModelMixin):
    author = models.ForeignKey(Profile, models.CASCADE, verbose_name="Пользователь", null=True, blank=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name="Чат", null=True, blank=True)
    text = models.TextField("ChatGPT preprompt", default="", blank=True)

    class Meta:
        verbose_name = "GPT препромпт"
        verbose_name_plural = "GPT препромпты"
        unique_together = ('author', 'chat', 'provider')


class Usage(TimeStampModelMixin, ProviderModelMixin):
    author = models.ForeignKey(Profile, models.CASCADE, verbose_name="Пользователь", null=True, db_index=True)
    cost = models.FloatField("Стоимость запроса", default=0)

    class Meta:
        verbose_name = "GPT использование"
        verbose_name_plural = "GPT использования"

    @classmethod
    def add_statistics(cls, sender: Profile, usage: GPTAPIUsage, provider: GPTProvider):
        Usage(
            author=sender,
            cost=usage.total_cost,
            provider=provider.name
        ).save()


class GPTSettings(TimeStampModelMixin):
    profile = models.OneToOneField(Profile, models.CASCADE, verbose_name="Пользователь", related_name="gpt_settings")

    # Если указан, то будет использоваться он, иначе - общий
    chat_gpt_key = models.CharField("Ключ ChatGPT", max_length=256, blank=True)
    chat_gpt_model = models.CharField("Модель ChatGPT", max_length=64, blank=True)

    claude_key = models.CharField("Ключ Claude", max_length=256, blank=True)
    claude_model = models.CharField("Модель Claude", max_length=64, blank=True)

    grok_key = models.CharField("Ключ Grok", max_length=256, blank=True)
    grok_model = models.CharField("Модель Grok", max_length=64, blank=True)

    class Meta:
        verbose_name = "GPT настройка"
        verbose_name_plural = "GPT настройки"
