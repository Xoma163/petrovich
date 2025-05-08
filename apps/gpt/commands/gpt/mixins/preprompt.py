from django.db.models import Q

from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.bot.models import Profile, Chat
from apps.gpt.models import Preprompt
from apps.gpt.protocols import GPTCommandProtocol


class GPTPrepromptMixin(GPTCommandProtocol):
    PREPROMPT_HELP_TEXT_ITEMS = [
        HelpTextArgument("препромпт [конфа]", "посмотреть текущий препромпт"),
        HelpTextArgument("препромпт [конфа] (текст)", "добавить препромпт"),
        HelpTextArgument("препромпт [конфа] удалить", "удаляет препромпт")
    ]

    EXTRA_TEXT = (
        "Порядок использования препромптов в конфах:\n"
        "1) Персональный препромт конфы\n"
        "2) Персональный препромт\n"
        "3) Препромпт конфы\n\n"
    )

    # MENU
    
    def menu_preprompt(self) -> ResponseMessageItem:
        """
        Установка/удаление препромпта
        """

        if len(self.event.message.args) > 1 and self.event.message.args[1] in ["chat", "conference", "конфа", "чат"]:
            self.check_conversation()
            q = Q(chat=self.event.chat, author=None)
            return self._preprompt(2, q, 'препромпт конфы')
        else:
            if self.event.is_from_pm:
                q = Q(chat=None, author=self.event.sender)
                return self._preprompt(1, q, 'персональный препромпт')
            else:
                q = Q(chat=self.event.chat, author=self.event.sender)
                return self._preprompt(1, q, 'персональный препромпт конфы')

    # HANDLERS

    def _preprompt(self, args_slice_index: int, q: Q, is_for: str) -> ResponseMessageItem:
        """
        Обработка препромптов
        """

        q &= Q(provider=self.provider.name)

        if len(self.event.message.args) > args_slice_index:
            # удалить
            if self.event.message.args[args_slice_index] == "удалить":
                Preprompt.objects.filter(q).delete()
                rmi = ResponseMessageItem(f"Удалил {is_for}")
            # обновить/создать
            else:
                preprompt = " ".join(self.event.message.args_case[args_slice_index:])
                preprompt_obj, _ = Preprompt.objects.update_or_create(
                    defaults={'text': preprompt},
                    **dict(q.children)
                )
                rmi = ResponseMessageItem(f"Обновил {is_for}: {self.bot.get_formatted_text(preprompt_obj.text)}")
        # посмотреть
        else:
            try:
                preprompt = Preprompt.objects.get(q).text
                rmi = ResponseMessageItem(f"Текущий {is_for}: {self.bot.get_formatted_text(preprompt)}")
            except Preprompt.DoesNotExist:
                rmi = ResponseMessageItem(f"Текущий {is_for} не задан")
        return rmi

    # COMMON UTILS
    
    def get_preprompt(self, sender: Profile, chat: Chat) -> str | None:
        """
        Получить препромпт под текущую ситуацию (персональный в чате,в чате,в лс)
        """

        if chat:
            variants = [
                Q(author=sender, chat=chat, provider=self.provider.name),
                Q(author=None, chat=chat, provider=self.provider.name),
            ]
        else:
            variants = [
                Q(author=sender, chat=None, provider=self.provider.name),
            ]

        for q in variants:
            try:
                return Preprompt.objects.get(q).text
            except Preprompt.DoesNotExist:
                continue
        return None
