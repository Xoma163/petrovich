from django.contrib.auth.models import Group
from django.core.files import File
from django.db import models
from django.utils.html import format_html

from apps.bot.api.gpt.models import GPTModels
from apps.bot.classes.const.consts import Platform as PlatformEnum, Role
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.service.mixins import TimeStampModelMixin


class Platform(models.Model):
    platform = models.CharField('Тип платформы', max_length=20, choices=PlatformEnum.choices())

    def get_platform_enum(self):
        if not self.platform:
            return None
        return [x for x in PlatformEnum if x.name == self.platform][0]

    class Meta:
        abstract = True


class BaseSettings(models.Model):
    # celebrate_bday
    class Meta:
        abstract = True


class ChatSettings(BaseSettings, TimeStampModelMixin):
    no_mention = models.BooleanField('Работа без упоминания в конфе', default=False)
    need_turett = models.BooleanField('Слать туреттные сообщения', default=False)
    celebrate_bday = models.BooleanField('Поздравлять с Днём рождения', default=False)
    recognize_voice = models.BooleanField('Распозновать голосовые автоматически', default=True)

    class Meta:
        verbose_name = "Настройка чата"
        verbose_name_plural = "Настройки чатов"

    def __str__(self):
        # return str(self.chat) if self.chat else ""
        return ""


class UserSettings(BaseSettings, TimeStampModelMixin):
    GPT_MODEL_CHOICES = [(x.name, x.verbose_name) for x in GPTModels.get_completions_models()]

    need_meme = models.BooleanField('Слать мемы по точному названию', default=False)
    need_reaction = models.BooleanField('Реагировать на неверные команды', default=True)
    use_swear = models.BooleanField("Использовать ругательства", default=True)

    celebrate_bday = models.BooleanField('Поздравлять с Днём рождения', default=True)
    show_birthday_year = models.BooleanField('Показывать год', default=True)
    use_mention = models.BooleanField('Использовать упоминания', default=True)

    # GPT
    # Если указан, то будет использоваться он, иначе - общий
    chat_gpt_key = models.CharField("Ключ GPT", max_length=256, blank=True)
    chat_gpt_model = models.CharField("модель GPT", max_length=64, choices=GPT_MODEL_CHOICES, blank=True)

    def get_gpt_model(self):
        return GPTModels.get_model_by_name(self.chat_gpt_model)

    class Meta:
        verbose_name = "Настройка профиля"
        verbose_name_plural = "Настройки профилей"

    def __str__(self) -> str:
        return str(self.profile) if self.profile else ""


class Chat(Platform, TimeStampModelMixin):
    chat_id = models.CharField('ID чата', max_length=20, default="")
    name = models.CharField('Название', max_length=256, default="", blank=True)
    is_banned = models.BooleanField('Забанен', default=False)

    # Настройки
    settings = models.OneToOneField(ChatSettings, verbose_name="Настройки", on_delete=models.CASCADE, null=True,
                                    related_name="chat")

    # Для статистики
    kicked = models.BooleanField("Бота кикнули", default=False)

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"
        unique_together = ('chat_id', 'platform',)

    def save(self, **kwargs):
        # auto create settings model
        is_new = self.id is None
        if is_new:
            cs = ChatSettings.objects.create()
            cs.save()
            self.settings = cs

        super(Chat, self).save(**kwargs)

    def delete(self, *args, **kwargs):
        if self.settings:
            self.settings.delete()
        super(Chat, self).delete(*args, **kwargs)

    def __str__(self):
        # return str(self.name) if self.name else f"id:{self.id}"
        return ""

class Profile(TimeStampModelMixin):
    GENDER_FEMALE = '1'
    GENDER_MALE = '2'
    GENDER_NONE = ''
    GENDER_CHOICES = (
        (GENDER_FEMALE, 'женский'),
        (GENDER_MALE, 'мужской'),
        (GENDER_NONE, 'не указан'))

    name = models.CharField('Имя', max_length=40, blank=True, null=True)
    surname = models.CharField('Фамилия', max_length=40, blank=True, null=True)
    nickname_real = models.CharField("Прозвище", max_length=40, blank=True)
    gender = models.CharField('Пол', max_length=2, blank=True, choices=GENDER_CHOICES)
    birthday = models.DateField('Дата рождения', null=True, blank=True)
    # Здесь такой странный ForeignKey потому что проблема импортов
    city = models.ForeignKey('service.City', models.SET_NULL, verbose_name='Город', null=True, blank=True)
    avatar = models.ImageField('Аватар', blank=True, upload_to="bot/users/avatar/")
    groups = models.ManyToManyField(Group, verbose_name="Группы")
    chats = models.ManyToManyField(Chat, verbose_name="Чаты", blank=True, related_name="users")

    # Настройки
    settings = models.OneToOneField(UserSettings, verbose_name="Настройки", on_delete=models.CASCADE, null=True,
                                    related_name="profile")

    api_token = models.CharField("Токен для API", max_length=100, blank=True)

    def save(self, **kwargs):
        # auto create settings model
        is_new = self.id is None
        if is_new:
            # auto create settings
            us = UserSettings.objects.create()
            self.settings = us

        super(Profile, self).save(**kwargs)

        if is_new:
            # auto add user group
            group_user = Group.objects.get(name=Role.USER.name)
            self.groups.add(group_user)

    def delete(self, *args, **kwargs):
        if self.settings:
            self.settings.delete()
        super(Profile, self).delete(*args, **kwargs)


    def set_avatar(self, att: PhotoAttachment = None):
        image = att.get_bytes_io_content()
        self.avatar.save(f"avatar_{str(self)}.{att.ext}", File(image))

    def add_role(self, role: Role):
        group = Group.objects.get(name=role.name)
        self.groups.add(group)

    def remove_role(self, role: Role):
        group = Group.objects.get(name=role.name)
        self.groups.remove(group)

    def check_role(self, role: Role):
        group = self.groups.filter(name=role.name)
        return group.exists()

    def get_roles(self) -> list[Role]:
        return [getattr(Role, x['name']) for x in self.groups.all().values()]

    def get_tg_user(self):
        return self.user.get(platform=PlatformEnum.TG.name)

    @property
    def is_female(self):
        return self.gender == self.GENDER_FEMALE

    @property
    def is_male(self):
        return self.gender == self.GENDER_MALE

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"
        ordering = ["name", "surname"]

    def __str__(self):
        if self.name and self.surname:
            return f"{self.name} {self.surname}"
        elif self.name:
            return str(self.name)
        else:
            return "Незарегистрированный пользователь"


class User(Platform, TimeStampModelMixin):
    user_id = models.CharField('ID пользователя', max_length=127)
    profile = models.ForeignKey(Profile, verbose_name="Профиль", related_name='user', null=True,
                                blank=True, on_delete=models.SET_NULL)
    nickname = models.CharField("Никнейм", max_length=40, blank=True, null=True)

    def show_url(self):
        if self.get_platform_enum() == PlatformEnum.TG:
            return format_html(f"<a href='https://t.me/{self.nickname}'>{self.platform}</a>")
        else:
            return self.platform

    show_url.short_description = "Ссылка"

    def show_user_id(self):
        if self.get_platform_enum() == PlatformEnum.TG:
            return self.user_id
        else:
            return self.user_id[:8] + "..."

    show_user_id.short_description = "user id"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

        unique_together = ('user_id', 'platform',)

    def __str__(self):
        return f"{self.profile} ({self.platform})"


class Bot(Platform, TimeStampModelMixin):
    bot_id = models.CharField('ID бота', max_length=20)
    name = models.CharField('Имя', max_length=40)
    avatar = models.ImageField('Аватар', blank=True, upload_to="bot/bot/avatar/")

    class Meta:
        verbose_name = "Бот"
        verbose_name_plural = "Боты"

        unique_together = ('bot_id', 'platform',)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return f"Неопознанный бот #{self.id}"
