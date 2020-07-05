from django.contrib import admin

# Register your models here.
from apps.bot.models import VkUser, VkChat, VkBot, APIUser, APITempUser


@admin.register(VkUser)
class VkUserAdmin(admin.ModelAdmin):
    list_display = (
        'user_id', 'name', 'surname', 'nickname', 'nickname_real', 'gender', 'birthday', 'city',
        # 'is_admin', 'is_moderator', 'is_student', 'is_banned', 'is_minecraft', 'is_terraria'
    )
    list_filter = ('gender',
                   ('city', admin.RelatedOnlyFieldListFilter),
                   ('groups', admin.RelatedOnlyFieldListFilter),
                   'chats__name')
    search_fields = ['name', 'surname', 'nickname', 'nickname_real', 'id']


@admin.register(VkChat)
class VkChatAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'name', 'admin', 'need_reaction')


@admin.register(VkBot)
class VkBotAdmin(admin.ModelAdmin):
    list_display = ('bot_id', 'name',)


@admin.register(APIUser)
class APIUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'vk_user', 'vk_chat')


@admin.register(APITempUser)
class APITempUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'vk_user', 'vk_chat', 'code', 'tries')
