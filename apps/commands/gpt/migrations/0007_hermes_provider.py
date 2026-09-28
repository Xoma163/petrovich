from django.db import migrations, models


def create_hermes_provider(apps, schema_editor):
    Provider = apps.get_model("gpt", "Provider")
    CompletionsModel = apps.get_model("gpt", "CompletionsModel")
    provider, _ = Provider.objects.get_or_create(name="hermes")
    CompletionsModel.objects.get_or_create(
        provider=provider,
        name="hermes-agent",
        defaults={
            "is_default": True,
            "input_1m_token_cost": 0,
            "input_cached_1m_token_cost": 0,
            "output_1m_token_cost": 0,
            "web_search_1k_token_cost": 0,
        },
    )


class Migration(migrations.Migration):
    dependencies = [("gpt", "0006_remove_imageeditmodel_unique_name_width_height_image_edit_and_more")]

    operations = [
        migrations.AlterField(
            model_name="provider",
            name="name",
            field=models.CharField(
                choices=[("chatgpt", "CHATGPT"), ("grok", "GROK"), ("qwen", "QWEN"), ("hermes", "HERMES")],
                max_length=32,
                unique=True,
                verbose_name="Провайдер",
            ),
        ),
        migrations.RunPython(create_hermes_provider, migrations.RunPython.noop),
    ]
