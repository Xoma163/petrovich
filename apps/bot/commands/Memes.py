from django.core.paginator import Paginator

from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.commands.Meme import get_tanimoto_memes
from apps.service.models import Meme as MemeModel


def get_memes_names(memes, sender):
    if sender.check_role(Role.MODERATOR):
        meme_names = [f"{meme.name} (id - {meme.id})" for meme in memes]
    else:
        meme_names = [meme.name for meme in memes]
    return meme_names


class Memes(CommonCommand):
    def __init__(self):
        names = ["мемы"]
        help_text = "Мемы - список мемов"
        detail_help_text = "Мемы [страница=1] - присылает список мемов на странице\n" \
                           "Мемы (поисковая фраза) - присылает список мемов, подходящих поисковому запросу\n\n"

        super().__init__(names, help_text, detail_help_text)

    def start(self):
        try:
            if self.event.args:
                self.int_args = [0]
                self.parse_int()
                page = self.event.args[0]
            else:
                page = 1
            memes = MemeModel.objects.filter(approved=True)

            p = Paginator(memes, 20)

            if page <= 0:
                page = 1
            if page > p.num_pages:
                page = p.num_pages

            msg_header = f"Страница {page}/{p.num_pages}"

            memes_on_page = p.page(page)
            meme_names = get_memes_names(memes_on_page, self.event.sender)
            msg_body = ";\n".join(meme_names)
            if len(meme_names) > 0:
                msg_body += '.'

            if page != p.num_pages:
                on_last_page = p.per_page * page
            else:
                on_last_page = p.count
            msg_footer = f'----{p.per_page * (page - 1) + 1}/{on_last_page}----'
            msg = f"{msg_header}\n\n{msg_body}\n\n{msg_footer}"
            return msg
        except RuntimeWarning:
            memes = MemeModel.objects
            for arg in self.event.args:
                memes = memes.filter(name__icontains=arg)
            if len(memes) == 0:
                raise RuntimeWarning("Не нашёл мемов по заданному запросу")
            memes = get_tanimoto_memes(memes, self.event.original_args)
            memes_sliced = memes[:20]
            meme_names = get_memes_names(memes_sliced, self.event.sender)
            meme_names_str = ";\n".join(meme_names)
            if len(memes) > len(memes_sliced):
                meme_names_str += "\n..."
            elif len(memes) > 0:
                meme_names_str += '.'
            return f"{meme_names_str}\n\nВсего - {len(memes)}"
