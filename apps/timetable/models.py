from django.db import models

# Create your models here.
from apps.bot.models import Chat


class Group(models.Model):
    number = models.PositiveIntegerField("Номер группы", help_text="4 цифры")
    title = models.CharField("Название группы", help_text="прост так", blank=True, max_length=100)
    conference = models.ForeignKey(Chat, on_delete=models.SET_NULL, null=True, verbose_name="Конфа")

    def __str__(self):
        return f"{self.number}"

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"
        ordering = ['number']


class Teacher(models.Model):
    name = models.CharField("ФИО преподавателя", help_text="Иванов И.И.", max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"
        ordering = ['name']


class Cabinet(models.Model):
    number = models.CharField("Номер кабинета", max_length=100, help_text="***-* или другое")

    def __str__(self):
        return self.number

    class Meta:
        verbose_name = "Кабинет"
        verbose_name_plural = "Кабинеты"
        ordering = ['number']


class Discipline(models.Model):
    name = models.CharField("Название", help_text="Полное название пары без сокращений", max_length=200)
    short_name = models.CharField("Название сокращённое",
                                  help_text="Сокращенное название (если оставить пустым, то сгенерируется автоматически)",
                                  blank=True, max_length=50)

    def save(self, *args, **kwargs):
        if not self.short_name:
            name_list = self.name.split(' ')
            short_name = ""
            for word in name_list:
                if word.lower() == "и":
                    short_name += word[0].lower()
                else:
                    short_name += word[0].upper()
            self.short_name = short_name

        super(Discipline, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Дисциплина"
        verbose_name_plural = "Дисциплины"
        ordering = ['name']


class Lesson(models.Model):
    LESSONS_NUMBER_1 = "1"
    LESSONS_NUMBER_2 = "2"
    LESSONS_NUMBER_3 = "3"
    LESSONS_NUMBER_4 = "4"
    LESSONS_NUMBER_5 = "5"
    LESSONS_NUMBER_6 = "6"
    LESSONS_NUMBER_7 = "7"
    LESSONS_NUMBER_8 = "8"

    LESSONS_NUMBERS = (
        (LESSONS_NUMBER_1, "1. 8:00-9:35"),
        (LESSONS_NUMBER_2, "2. 9:45-11:20"),
        (LESSONS_NUMBER_3, "3. 11:30-13:05"),
        (LESSONS_NUMBER_4, "4. 13:30-15:05"),
        (LESSONS_NUMBER_5, "5. 15:15-16:50"),
        (LESSONS_NUMBER_6, "6. 17:00-18:35"),
        (LESSONS_NUMBER_7, "7. 18:45-20:15"),
        (LESSONS_NUMBER_8, "8. 20:25-21:55"),
    )

    LESSON_TYPE_LECTURE = "1"
    LESSON_TYPE_PRACTICE = "2"
    LESSON_TYPE_LABORATORY_WORK = "3"
    LESSON_TYPE_OTHER = "4"

    LESSONS_TYPES = (
        (LESSON_TYPE_LECTURE, "Лекция"),
        (LESSON_TYPE_PRACTICE, "Практика"),
        (LESSON_TYPE_LABORATORY_WORK, "Лабораторная работа"),
        (LESSON_TYPE_OTHER, "Другое"),
    )
    WEEK_NUMBER_1 = "1"
    WEEK_NUMBER_2 = "2"
    WEEK_NUMBER_3 = "3"
    WEEK_NUMBER_4 = "4"

    WEEK_NUMBERS = (
        (WEEK_NUMBER_1, "Лекция"),
        (WEEK_NUMBER_2, "Практика"),
        (WEEK_NUMBER_3, "Лабораторная работа"),
        (WEEK_NUMBER_4, "Другое"),
    )

    group = models.ForeignKey(Group, models.SET_NULL, verbose_name="Группа", null=True)
    lesson_number = models.CharField("Номер пары", choices=LESSONS_NUMBERS, max_length=2)
    teacher = models.ForeignKey(Teacher, models.SET_NULL, verbose_name="Преподаватель", null=True)
    lesson_type = models.CharField("Тип пары", choices=LESSONS_TYPES, max_length=2)
    cabinet = models.ForeignKey(Cabinet, on_delete=models.SET_NULL, verbose_name="Кабинет", null=True)
    week_number = models.CharField("Номер недели", choices=WEEK_NUMBERS, max_length=2)

    def __str__(self):
        return f"{self.group} {self.lesson_number} {self.teacher} {self.lesson_type} {self.cabinet}"

    class Meta:
        verbose_name = "Пара"
        verbose_name_plural = "Пары"
