from django.core.paginator import Paginator
from django.db.models import Q

from apps.bot.consts import Role
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.commands.command import Command
from apps.commands.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.commands.meme.models import Meme as MemeModel
from apps.shared.exceptions import PWarning


class Memes(Command):
    name = "мемы"

    help_text = HelpText(
        commands_text="список мемов",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextArgument(
                    "[фраза для поиска] [страница=1]",
                    "присылает список мемов, подходящих поисковому запросу на странице"
                )
            ])
        ]
    )

    PER_PAGE = 20

    def start(self) -> ResponseMessage:
        q = Q()
        if self.event.message.args:
            self.int_args = [-1]
            try:
                self.parse_int()
                args = self.event.message.args[:-1]
                page = self.event.message.args[-1]
            except PWarning:
                args = self.event.message.args
                page = 1
            for arg in args:
                q &= Q(name__icontains=arg)
        else:
            page = 1

        q_exclude = Q()
        if not self.event.sender.check_role(Role.TRUSTED):
            q_exclude &= Q(for_trusted=True)
        memes = MemeModel.objects.filter(approved=True).filter(q).exclude(q_exclude)
        if len(memes) == 0:
            raise PWarning("Не нашёл мемов по заданному запросу")

        p = Paginator(memes, self.PER_PAGE)

        if page <= 0:
            page = 1
        if page > p.num_pages:
            page = p.num_pages

        msg_header = f"Страница {page}/{p.num_pages}"
        memes_on_page = p.page(page)
        memes_names = self.get_memes_names(memes_on_page)
        msg_body = ";\n".join(memes_names)
        if len(memes_names) > 0:
            msg_body += '.'
        if page != p.num_pages:
            on_last_page = p.per_page * page
        else:
            on_last_page = p.count
        msg_footer = f'----{p.per_page * (page - 1) + 1}-{on_last_page}----'
        answer = f"{msg_header}\n\n{msg_body}\n\n{msg_footer}"
        return ResponseMessage(ResponseMessageItem(text=answer))

    def get_memes_names(self, memes) -> list:
        return [f"{self.bot.get_formatted_text_line(meme.name)} (id - {meme.id})" for meme in memes]
