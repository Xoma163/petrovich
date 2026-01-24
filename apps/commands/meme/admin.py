from django.contrib import admin

from apps.commands.meme.models import Meme
from apps.shared.mixins import TimeStampAdminMixin


# Register your models here.
@admin.register(Meme)
class MemeAdmin(TimeStampAdminMixin):
    list_display = (
        'id',
        'name',
        'author',
        'approved',
        'type',
        'uses',
        'inline_uses',
        'link',
        'has_tg_file_id',
        "for_trusted"
    )
    search_fields = (
        'name',
        'link'
    )
    list_filter = (
        ('author', admin.RelatedOnlyFieldListFilter),
        'type',
        'approved',
        'for_trusted',
        ('file', admin.EmptyFieldListFilter)
    )
    list_select_related = (
        'author',
    )
    ordering = (
        "name",
    )

    @admin.display(description="Есть tg_file_id", boolean=True)
    def has_tg_file_id(self, obj: Meme) -> bool:
        return bool(obj.tg_file_id)

    @admin.display(description="Есть файл", boolean=True)
    def has_file(self, obj: Meme) -> bool:
        return bool(obj.file)
