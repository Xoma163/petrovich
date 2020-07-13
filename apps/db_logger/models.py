import logging

from django.db import models

from apps.bot.models import Users, Chat


class Logger(models.Model):
    LOG_LEVELS = (
        (logging.NOTSET, 'NOTSET'),
        (logging.DEBUG, "DEBUG"),
        (logging.INFO, "INFO"),
        (logging.WARNING, "WARNING"),
        (logging.ERROR, "ERROR"),
        (logging.FATAL, "FATAL"),
    )

    logger_name = models.CharField("Логгер", max_length=100)
    level = models.PositiveSmallIntegerField("Уровень", choices=LOG_LEVELS, default=logging.ERROR, db_index=True)
    create_datetime = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    event = models.TextField("Запрос пользователя", blank=True, null=True)

    user_msg = models.TextField("Сообщение пользователя", blank=True, null=True)
    msg = models.TextField("Сообщение")

    sender = models.ForeignKey(Users, verbose_name="Пользователь", on_delete=models.SET_NULL, null=True)
    chat = models.ForeignKey(Chat, verbose_name="Чат", on_delete=models.SET_NULL, null=True)

    result = models.TextField("Результат выполнения", blank=True, null=True)
    exception = models.TextField("Ошибка", blank=True, null=True)
    traceback = models.TextField(blank=True, null=True, verbose_name="Traceback")

    def __str__(self):
        return self.msg

    class Meta:
        # abstract = True
        ordering = ('-create_datetime',)


class MovementLog(models.Model):
    EVENTS_CHOICES = (('home', 'дома'),
                      ('work', 'работа'),
                      ('university', 'университет'),
                      ('somewhere', 'где-то'))
    date = models.DateTimeField(verbose_name="Дата", auto_now_add=True, blank=True)
    imei = models.CharField(verbose_name='IMEI', max_length=20, null=True)
    author = models.ForeignKey(Users, verbose_name="Автор", on_delete=models.SET_NULL, null=True)
    event = models.CharField(verbose_name='Событие', choices=EVENTS_CHOICES,
                             max_length=20,
                             null=True)
    msg = models.CharField(verbose_name='Сообщение', max_length=2000)
    success = models.BooleanField(verbose_name='Отправлено', default=False)

    @classmethod
    def create(cls, imei, author, event, msg, success):
        log = cls(imei=imei, author=author, event=event, msg=msg, success=success)
        return log

    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "Журнал событий"
        ordering = ["-date"]

    def __str__(self):
        return str(self.id)
