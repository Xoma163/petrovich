def clone(model_admin, request, queryset):
    for ad in queryset:
        ad.pk = None
        ad.save()


clone.short_description = "Склонировать"
