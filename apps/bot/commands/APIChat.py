from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.models import APITempUser, APIUser


# ToDo: DEPRECATED
class APIChat(CommonCommand):
    def __init__(self):
        names = ["чат"]
        help_text = "Чат - привязывает чат к API"
        detail_help_text = "Чат - привязывает чат к API\n" \
                           "Чат привязать (название конфы) - отправляет код в выбранную конфу\n" \
                           "Чат отвязать (название конфы) - отправляет код в выбранную конфу\n" \
                           "Чат код (код) - привязывает чат к пользователю"
        super().__init__(names, help_text, detail_help_text, args=1, enabled=False)

    def start(self):
        if self.event.sender.user_id == "ANONYMOUS":
            raise RuntimeWarning("Анонимный пользователь не может иметь привязанных чатов")

        if self.event.args[0] == 'привязать':
            self.check_args(2)
            chat_name = self.event.original_args.split(' ', 1)[1]
            chat_with_user = self.bot.get_one_chat_with_user(chat_name, self.event.sender.user_id)

            APITempUser.objects.filter(user_id=self.event.yandex['client_id']).delete()
            yandex_temp_user = APITempUser(
                user_id=self.event.yandex['client_id'],
                user=self.event.sender,
                chat=chat_with_user,
            )
            yandex_temp_user.save()
            msg = f"Код для пользователя {self.event.sender}\n" \
                  f"{yandex_temp_user.code}"

            self.bot.send_message(chat_with_user.chat_id, msg)
            return "Отправил код. Пришлите мне его. Чат код {код}"
        elif self.event.args[0] == 'код':
            self.check_args(2)
            code = self.event.args[1]
            yandex_temp_user = APITempUser.objects.filter(user_id=self.event.yandex['client_id'],
                                                          user=self.event.sender,
                                                          chat__isnull=False).first()
            if not yandex_temp_user:
                raise RuntimeWarning("Не нашёл привязок. Привяжите /чат привязать {название конфы}")
            if yandex_temp_user.tries <= 0:
                raise RuntimeWarning("Вы превысили максимальное число попыток")

            if yandex_temp_user.code != code:
                yandex_temp_user.tries -= 1
                yandex_temp_user.save()
                raise RuntimeWarning(f"Неверный код. Осталось попыток - {yandex_temp_user.tries}")

            yandex_users = APIUser.objects.filter(user=yandex_temp_user.user)
            if len(yandex_users) == 0:
                raise RuntimeWarning("Не нашёл пользователя APIUser, оч странная хрень. Напишите разрабу")
            for yandex_user in yandex_users:
                yandex_user.chat = yandex_temp_user.chat
                yandex_user.save()
            yandex_temp_user.delete()
            return "Успешно привязал"
        elif self.event.args[0] == 'отвязать':
            yandex_users = APIUser.objects.filter(user=self.event.sender)
            if len(yandex_users) == 0:
                raise RuntimeWarning("Не нашёл пользователя APIUser, оч странная хрень. Напишите разрабу")
            for yandex_user in yandex_users:
                yandex_user.chat = None
                yandex_user.save()
            return "Успешно отвязал"
        else:
            raise RuntimeWarning("Не понял. Доступно: Чат привязать/код/отвязать.")
