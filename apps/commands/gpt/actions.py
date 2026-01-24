from django.contrib import admin, messages
from django.db import transaction

from .models import VisionModel


# GPT GENERATED
@admin.action(description="Копировать в Vision (создать/обновить)")
def copy_completions_to_vision(modeladmin, request, queryset):
    created = updated = errors = 0

    # Helper: собрать данные для создания/обновления VisionModel
    def build_field_values(src_instance):
        values = {}
        for field in VisionModel._meta.get_fields():
            # Пропускаем автоматические и реляционные поля, которые не хотим напрямую устанавливать
            if getattr(field, "auto_created", False):
                continue
            if getattr(field, "primary_key", False):
                continue
            if getattr(field, "many_to_many", False):
                continue
            if getattr(field, "one_to_many", False) or getattr(field, "one_to_one", False) and field.auto_created:
                continue
            # Пропускаем поля с auto_now/auto_now_add
            if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
                continue

            # Поле может быть ForeignKey или обычным полем
            # field.name — имя поля (например 'provider'), attname — 'provider_id' для FK
            name = field.name
            # Берём значение если атрибут присутствует у исходной модели
            if hasattr(src_instance, name):
                values[name] = getattr(src_instance, name)
        return values

    for obj in queryset:
        data = build_field_values(obj)
        # Убедимся, что ключи для поиска присутствуют (в вашем случае unique constraint: name+provider)
        lookup = {}
        for key in ("name", "provider"):
            if key in data:
                lookup[key] = data.pop(key)
        if not lookup:
            errors += 1
            continue

        try:
            with transaction.atomic():
                vm, created_flag = VisionModel.objects.update_or_create(defaults=data, **lookup)
                if created_flag:
                    created += 1
                else:
                    updated += 1

                # Копируем M2M поля отдельно (если они есть и присутствуют у исходного объекта)
                for m2m in VisionModel._meta.many_to_many:
                    if hasattr(obj, m2m.name):
                        getattr(vm, m2m.name).set(getattr(obj, m2m.name).all())
        except Exception as exc:
            errors += 1

    msg = f"Скопировано: {created}, обновлено: {updated}, ошибок: {errors}"
    modeladmin.message_user(request, msg, level=messages.INFO)
