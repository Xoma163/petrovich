from django.contrib import admin

# Register your models here.
from apps.bot.models import Users, Chat, Bot, APIUser, APITempUser


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'surname', 'nickname', 'nickname_real', 'gender', 'birthday', 'city',
    )
    list_filter = ('platform', 'gender',
                   ('city', admin.RelatedOnlyFieldListFilter),
                   ('groups', admin.RelatedOnlyFieldListFilter),
                   'chats__name',)
    search_fields = ['name', 'surname', 'nickname', 'nickname_real', 'id']


admin.site.register(Users, UserAdmin)


class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'admin', 'need_reaction', 'platform',)
    list_filter = ('platform',)


admin.site.register(Chat, ChatAdmin)


class BotAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'platform',)
    list_filter = ('platform',)

admin.site.register(Bot, BotAdmin)


@admin.register(APIUser)
class APIUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'chat')


@admin.register(APITempUser)
class APITempUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'chat', 'code', 'tries')
