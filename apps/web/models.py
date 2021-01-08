from django.db import models


class CalculatorUser(models.Model):
    name = models.CharField("Имя", max_length=127)

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

    def __str__(self):
        return str(self.name)


class CalculatorProduct(models.Model):
    class UnitOfMeasurement(models.TextChoices):
        KG = "kg", "кг"
        G = "g", "г"
        PIECE = "piece", "шт"
        JAR = "jar", "б"
        PACKING = "packing", 'уп'
        LITER = "liter", 'л'

    name = models.CharField("Название", max_length=127)
    count = models.PositiveIntegerField("Количество")
    uom = models.CharField(
        max_length=10,
        choices=UnitOfMeasurement.choices,
        default=UnitOfMeasurement.PIECE,
        verbose_name='Единица измерения',
    )
    is_bought = models.BooleanField("Куплено", default=False)
    bought_by = models.ForeignKey(CalculatorUser, on_delete=models.SET_NULL, null=True, verbose_name="Кем куплено", blank=True)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"

    def __str__(self):
        return str(self.name)


class CalculatorSession(models.Model):
    name = models.CharField("Название", max_length=127)
    users = models.ManyToManyField(CalculatorUser, verbose_name="Пользователи", blank=True)
    products = models.ManyToManyField(CalculatorProduct, verbose_name="Товары", blank=True)

    class Meta:
        verbose_name = "сессия"
        verbose_name_plural = "сессии"

    def __str__(self):
        return str(self.name)
