from django.db import models


class CalculatorUser(models.Model):
    name = models.CharField("Имя", max_length=127,blank=True)

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"
        ordering = ["name"]

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

    name = models.CharField("Название", max_length=127, blank=True)
    count = models.PositiveIntegerField("Количество", blank=True)
    uom = models.CharField(
        max_length=10,
        choices=UnitOfMeasurement.choices,
        default=UnitOfMeasurement.PIECE,
        verbose_name='Единица измерения',
        null=True
    )
    is_bought = models.BooleanField("Куплено", default=False)
    bought_by = models.ForeignKey(CalculatorUser, on_delete=models.SET_NULL, null=True, verbose_name="Кем куплено",
                                  blank=True)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2, blank=True)

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"

    def __str__(self):
        return str(self.name)


class CalculatorSession(models.Model):
    name = models.CharField("Название", max_length=127)
    users = models.ManyToManyField(CalculatorUser, verbose_name="Пользователи", blank=True)
    products = models.ManyToManyField(CalculatorProduct, verbose_name="Товары", blank=True)

    def calculate(self):
        users = {u.name: {'money': 0} for u in self.users.all()}

        for product in self.products.all():
            users[product.bought_by.name]['money'] += float(product.price)

        users = dict(sorted(users.items(), key=lambda x: x[1]['money'], reverse=True))
        total_money = sum([users[user]['money'] for user in users])
        avg_money = round(total_money / len(users))

        for key in users:
            user = users[key]
            user['debt'] = round(avg_money - user['money'])

        result_list = {
            'transactions': [],
            'currency': 'руб',
            'total_money': round(total_money, 2),
            'avg_money': round(avg_money, 2)
        }

        first_user = list(users)[0]
        for i, user in enumerate(users):
            if i == 0:
                continue
            if users[user]['debt'] > 0:
                result_list['transactions'].append(
                    {'from': user, 'to': first_user, 'money': users[user]['debt']})
            else:
                result_list['transactions'].append(
                    {'from': first_user, 'to': user, 'money': -users[user]['debt']})

        return result_list

    class Meta:
        verbose_name = "сессия"
        verbose_name_plural = "сессии"

    def __str__(self):
        return str(self.name)
