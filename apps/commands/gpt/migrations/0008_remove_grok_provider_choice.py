from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("gpt", "0007_hermes_provider")]

    operations = [
        migrations.AlterField(
            model_name="provider",
            name="name",
            field=models.CharField(
                choices=[("chatgpt", "CHATGPT"), ("qwen", "QWEN"), ("hermes", "HERMES")],
                max_length=32,
                unique=True,
                verbose_name="Провайдер",
            ),
        ),
    ]
