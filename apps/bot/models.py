from typing import List

from django.contrib.auth.models import Group
from django.core.files import File
from django.db import models
from django.utils.html import format_html

from apps.bot.classes.const.consts import Platform as PlatformEnum, Role
from apps.bot.classes.messages.attachments.photo import PhotoAttachment


class Platform(models.Model):
    platform = models.CharField('Тип платформы', max_length=20, choices=PlatformEnum.choices())

    def get_platform_enum(self):
        if not self.platform:
            return None
        return [x for x in PlatformEnum if x.name == self.platform][0]

    class Meta:
        abstract = True


class BaseSettings(models.Model):
    gpt_preprompt = models.TextField("ChatGPT preprompt", default="")

    class Meta:
        abstract = True


class ChatSettings(BaseSettings):
    mentioning = models.BooleanField('Работа без упоминания в конфе', default=False)
    need_turett = models.BooleanField('Слать туреттные сообщения', default=False)
    celebrate_bday = models.BooleanField('Поздравлять с Днём рождения', default=False)
    recognize_voice = models.BooleanField('Распозновать голосовые автоматически', default=True)

    class Meta:
        verbose_name = "Настройка чата"
        verbose_name_plural = "Настройки чатов"

    def __str__(self):
        return str(self.chat)


class UserSettings(BaseSettings):
    need_meme = models.BooleanField('Слать мемы по точному названию', default=False)
    need_reaction = models.BooleanField('Реагировать на неверные команды', default=True)
    use_swear = models.BooleanField("Использовать ругательства", default=True)

    celebrate_bday = models.BooleanField('Поздравлять с Днём рождения', default=True)
    show_birthday_year = models.BooleanField('Показывать год', default=True)

    class Meta:
        verbose_name = "Настройка профиля"
        verbose_name_plural = "Настройки профилей"

    def __str__(self):
        return str(self.profile)

class Chat(Platform):
    id = models.AutoField(primary_key=True)
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
        ordering = ["name"]

        unique_together = ('chat_id', 'platform',)

    def save(self, **kwargs):
        # auto create settings model
        is_new = self.id is None
        if is_new:
            cs = ChatSettings.objects.create()
            cs.save()
            self.settings = cs

        super(Chat, self).save(**kwargs)

    def __str__(self):
        return str(self.name) if self.name else f"id:{self.id}"


class Profile(models.Model):
    GENDER_FEMALE = '1'
    GENDER_MALE = '2'
    GENDER_NONE = ''
    GENDER_CHOICES = (
        (GENDER_FEMALE, 'женский'),
        (GENDER_MALE, 'мужской'),
        (GENDER_NONE, 'не указан'))

    id = models.AutoField(primary_key=True)
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
            us = UserSettings.objects.create()
            us.save()
            self.settings = us
        super(Profile, self).save(**kwargs)

        if is_new:
            # auto create gamer
            from apps.games.models import Gamer
            Gamer.objects.create(profile=self)

            group_user = Group.objects.get(name=Role.USER.name)
            self.groups.add(group_user)


    def set_avatar(self, att: PhotoAttachment = None):
        image = att.get_bytes_io_content()
        self.avatar.save(f"avatar_{str(self)}.{att.ext}", File(image))

    def check_role(self, role: Role):
        group = self.groups.filter(name=role.name)
        return group.exists()

    def get_roles(self) -> List[Role]:
        return [getattr(Role, x['name']) for x in self.groups.all().values()]

    def get_tg_user(self):
        return self.user.get(platform=PlatformEnum.TG.name)

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


class User(Platform):
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
        ordering = ["profile"]

        unique_together = ('user_id', 'platform',)

    def __str__(self):
        return f"{self.profile} ({self.platform})"


class Bot(Platform):
    id = models.AutoField(primary_key=True)
    bot_id = models.CharField('ID бота', max_length=20)
    name = models.CharField('Имя', max_length=40)
    avatar = models.ImageField('Аватар', blank=True, upload_to="bot/bot/avatar/")

    class Meta:
        verbose_name = "Бот"
        verbose_name_plural = "Боты"
        ordering = ["id"]

        unique_together = ('bot_id', 'platform',)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return f"Неопознанный бот #{self.id}"
