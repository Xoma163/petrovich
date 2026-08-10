from apps.bot.consts import RoleEnum
from apps.bot.core.event.event import Event
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.models import Profile, User
from apps.commands.command import Command
from apps.shared.exceptions import PSkipContinue, PWarning
from apps.shared.utils.utils import get_admin_profile


class CheckTrustedRole(Command):
    ACCESS_REQUEST_COMMAND = "aq"
    ACCESS_APPROVE_COMMAND = "ay"
    ACCESS_REJECT_COMMAND = "an"
    KWARGS_PROFILE_KEY = "p"
    KWARGS_PEER_ID_KEY = "i"
    KWARGS_MESSAGE_THREAD_ID_KEY = "m"

    names = []
    # Обоснование: команда должна запускаться перед всеми остальными командами, но после экшенов
    priority = 99

    def accept(self, event: Event) -> bool:
        return True

    def start(self) -> ResponseMessage | None:
        if self.event.payload and self.event.message.command in [
            self.ACCESS_REQUEST_COMMAND,
            self.ACCESS_APPROVE_COMMAND,
            self.ACCESS_REJECT_COMMAND,
        ]:
            return self.process_access_request()

        if self.event.sender and not self.event.sender.check_role(RoleEnum.TRUSTED):
            button = self.bot.get_button("Запросить доступ", self.ACCESS_REQUEST_COMMAND)
            keyboard = self.bot.get_inline_keyboard([button])
            raise PWarning("Обратитесь за доступом к создателю бота.", keyboard=keyboard)
        raise PSkipContinue()

    def process_access_request(self) -> ResponseMessage | None:
        if self.event.message.command == self.ACCESS_REQUEST_COMMAND:
            return self.send_access_request_for_approval()
        if self.event.message.command in [self.ACCESS_APPROVE_COMMAND, self.ACCESS_REJECT_COMMAND]:
            return self.process_admin_decision()
        raise PSkipContinue()

    def send_access_request_for_approval(self) -> ResponseMessage:
        sender_user = self.event.user
        username = f"@{sender_user.nickname}" if sender_user and sender_user.nickname else "не указан"
        user_id = sender_user.user_id if sender_user else "не указан"
        text = (
            "Пользователь хочет получить доступ к боту:\n"
            f"Имя: {self.event.sender.name or 'не указано'}\n"
            f"Фамилия: {self.event.sender.surname or 'не указана'}\n"
            f"Никнейм: {username}\n"
            f"Профиль: {self.event.sender}\n"
            f"Telegram ID: {user_id}"
        )
        callback_kwargs = {
            self.KWARGS_PROFILE_KEY: self.event.sender.pk,
            self.KWARGS_PEER_ID_KEY: self.event.peer_id,
            self.KWARGS_MESSAGE_THREAD_ID_KEY: self.event.message_thread_id or 0,
        }
        button_approve = self.bot.get_button(
            "Принять",
            self.ACCESS_APPROVE_COMMAND,
            kwargs=callback_kwargs,
        )
        button_reject = self.bot.get_button(
            "Отклонить",
            self.ACCESS_REJECT_COMMAND,
            kwargs=callback_kwargs,
        )
        keyboard = self.bot.get_inline_keyboard([button_approve, button_reject], cols=2)

        admin_profile = get_admin_profile()
        if not admin_profile:
            raise PWarning("Не смог найти админа для запроса доступа.")

        try:
            admin_user = admin_profile.get_tg_user()
        except User.DoesNotExist:
            raise PWarning("Не смог найти телеграм админа для запроса доступа.")

        self.bot.send_response_message_item(
            ResponseMessageItem(text=text, peer_id=admin_user.user_id, keyboard=keyboard),
        )
        return ResponseMessage(ResponseMessageItem(text="Запрос доступа отправлен.", message_id=self.event.message.id))

    def process_admin_decision(self) -> ResponseMessage:
        self.check_sender(RoleEnum.ADMIN)
        try:
            profile_pk, peer_id, message_thread_id = self.get_admin_decision_data()
            profile = Profile.objects.get(pk=profile_pk)
        except (Profile.DoesNotExist, ValueError):
            raise PWarning("Пользователь для запроса доступа не найден.")
        approved = self.is_admin_approved()
        if approved:
            profile.add_role(RoleEnum.TRUSTED)

        user_text = "Доступ разрешён" if approved else "Доступ не разрешён"
        admin_text = f"Успешно {'разрешил' if approved else 'отклонил'} доступ для пользователя {profile}."
        return ResponseMessage(
            [
                ResponseMessageItem(text=admin_text, message_id=self.event.message.id),
                ResponseMessageItem(text=user_text, peer_id=peer_id, message_thread_id=message_thread_id),
            ],
        )

    def get_admin_decision_data(self) -> tuple[int, int, int | None]:
        kwargs = (self.event.payload.get("k") or {}) if self.event.payload else {}
        try:
            return (
                int(kwargs[self.KWARGS_PROFILE_KEY]),
                int(kwargs[self.KWARGS_PEER_ID_KEY]),
                int(kwargs.get(self.KWARGS_MESSAGE_THREAD_ID_KEY) or 0) or None,
            )
        except (KeyError, TypeError):
            raise PWarning("Кнопка запроса доступа устарела. Попросите пользователя отправить запрос ещё раз.")

    def is_admin_approved(self) -> bool:
        return self.event.message.command == self.ACCESS_APPROVE_COMMAND
