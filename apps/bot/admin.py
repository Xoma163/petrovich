from django.contrib import admin

# Register your models here.
from apps.bot.models import VkUser, VkChat, VkBot, APIUser, APITempUser, TgUser, TgChat, TgBot


class AbstractUserAdmin(admin.ModelAdmin):
    list_display = (
        'user_id', 'name', 'surname', 'nickname', 'nickname_real', 'gender', 'birthday', 'city',
    )
    list_filter = ('gender',
                   ('city', admin.RelatedOnlyFieldListFilter),
                   ('groups', admin.RelatedOnlyFieldListFilter),
                   'chats__name')
    search_fields = ['name', 'surname', 'nickname', 'nickname_real', 'id']


admin.site.register(VkUser, AbstractUserAdmin)
admin.site.register(TgUser, AbstractUserAdmin)


class AbstractChatAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'name', 'admin', 'need_reaction')


admin.site.register(VkChat, AbstractChatAdmin)
admin.site.register(TgChat, AbstractChatAdmin)


class AbstractBotAdmin(admin.ModelAdmin):
    list_display = ('bot_id', 'name',)


admin.site.register(VkBot, AbstractBotAdmin)
admin.site.register(TgBot, AbstractBotAdmin)


@admin.register(APIUser)
class APIUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'vk_user', 'vk_chat')


@admin.register(APITempUser)
class APITempUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'vk_user', 'vk_chat', 'code', 'tries')
