import datetime
from threading import Lock

from django.db.models import QuerySet

from apps.bot.consts import PlatformEnum, RoleEnum
from apps.bot.core.bot.tg_bot.tg_bot import TgBot
from apps.bot.core.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.models import Role
from apps.commands.command import Command
from apps.commands.games.models import PetrovichGame, PetrovichUser
from apps.commands.help_text import HelpTextItem, HelpText, HelpTextArgument
from apps.shared.exceptions import PWarning
from apps.shared.utils.utils import localize_datetime, remove_tz, random_event
from petrovich.settings import DEFAULT_TIME_ZONE

lock = Lock()


class Petrovich(Command):
    name = "петрович"
    names = ['петровна']

    help_text = HelpText(
        commands_text="мини-игра, определяющая кто Петрович дня",
        help_texts=[
            HelpTextItem(RoleEnum.USER, [
                HelpTextArgument(None, "мини-игра, определяющая кто Петрович дня"),
                HelpTextArgument("рег", "регистрация в игре"),
                HelpTextArgument("дерег", "дерегистрация в игре"),
                HelpTextArgument("игроки", "список зарегистрированных участников")
            ])
        ]
    )

    conversation = True
    platforms = [PlatformEnum.TG]

    bot: TgBot

    def start(self) -> ResponseMessage:
        if self.event.message.args:
            arg0 = self.event.message.args[0]
        else:
            arg0 = None
        menu = [
            [['рег', 'регистрация'], self.menu_reg],
            [['дерег'], self.menu_dereg],
            [['игроки'], self.menu_gamers],
            [['default'], self.menu_play]
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def menu_reg(self) -> ResponseMessage:
        p_user = PetrovichUser.objects.filter(profile=self.event.sender, chat=self.event.chat).first()
        if p_user is not None:
            if not p_user.active:
                p_user.active = True
                p_user.save()
                answer = "Возвращаю тебя в строй"
            else:
                answer = "Ты уже зарегистрирован"
            return ResponseMessage(ResponseMessageItem(text=answer))

        PetrovichUser.objects.create(profile=self.event.sender, chat=self.event.chat, active=True)
        answer = "Регистрация прошла успешно"
        return ResponseMessage(ResponseMessageItem(text=answer))

    def menu_dereg(self) -> ResponseMessage:
        p_user = PetrovichUser.objects.filter(profile=self.event.sender, chat=self.event.chat).first()
        if p_user is not None and p_user.active:
            p_user.active = False
            p_user.save()
            answer = "Ок"
        else:
            answer = "А ты и не зареган"
        return ResponseMessage(ResponseMessageItem(text=answer))

    def menu_gamers(self) -> ResponseMessage:
        petrovich_gamers = self._get_petrovich_gamers()
        if petrovich_gamers.count() == 0:
            answer = "Нет зарегистрированных игроков"
        else:
            gamers_str = "\n".join([str(x) for x in petrovich_gamers])
            answer = f"Список игроков:\n{gamers_str}"
        return ResponseMessage(ResponseMessageItem(text=answer))

    def menu_play(self) -> ResponseMessage:
        with lock:
            datetime_now = localize_datetime(datetime.datetime.now(datetime.UTC), DEFAULT_TIME_ZONE)
            winner_today = PetrovichGame.objects.filter(chat=self.event.chat).order_by('-created_at').first()

            if winner_today:
                datetime_last = localize_datetime(remove_tz(winner_today.created_at), DEFAULT_TIME_ZONE)
                if (datetime_now.date() - datetime_last.date()).days <= 0:
                    winner_gender = "Петровна" if winner_today.profile.gender == '1' else "Петрович"
                    answer = f"{winner_gender} дня - {winner_today.profile}"
                    return ResponseMessage(ResponseMessageItem(text=answer))

            petrovich_gamers = self._get_petrovich_gamers()
            winner = petrovich_gamers.order_by("?").first()

            if not winner:
                button = self.bot.get_button('Зарегистрироваться', self.name, ['рег'])
                keyboard = self.bot.get_inline_keyboard([button])
                raise PWarning(
                    f"Нет участников игры. Зарегистрируйтесь! {self.bot.get_formatted_text_line('/петрович рег')}",
                    keyboard=keyboard
                )
            winner_profile = winner.profile

            winner_petrovich = PetrovichGame(profile=winner_profile, chat=self.event.chat)
            winner_petrovich.save()

            winner_gender = "Петровна" if winner_profile.gender == '1' else "Петрович"
            first_answer = random_event([
                "Такс такс такс, кто тут у нас",
                "*барабанная дробь*",
                "Вы готовы узнать победителя голодных игр?",
                "Ну шо, погнали",
                "Вы не поверите...",
                "Опять вы в игрульки свои играете да? Ну ладно",
                "А КТО ЭТО У НАС ТУТ ТАКОЙ СЕГОДНЯ",
                "Определяем обладателя бесплатного проездного на один день в метро",
                "Ой, кто это тут у нас такой? Петрович дня, конечно же!",
                "О, смотрите, кто тут у нас! Петрович дня, выходи!",
                "Сканирую базу... Оп, нашел Петровича дня!",
                "Кто просил Рандомную Справедливость™? Держите своего Петровича дня!",
                "Магический шар говорит: \"Это он, Петрович дня!\"",
                "Внимание! Система выбрала жертву дня",
                "Есть контакт! Приземляемся... И вот, на радость нам всем!",
                "Дамы и господа, вашему вниманию представляется эксклюзивный Петрович дня!",
                "Итак, кого из вас сегодня почитать?",
                "Колесо фортуны вращается... останавливается...",
                "Бинго! Нашлась особь для титула Петрович дня:",
                "Опа! Сюрприз-мороженое сегодня без очереди получает:",
                "Свечи гаснут... а suspense растет!",
                "Ваши ставки, господа. Пора вскрыть карты",
                "И звезды ночи сегодня замигают для...",
                "Чей это кристалл судьбы блестит ярче всех сегодня?",
                "Так, стоп, хватит держать вас в напряжении!"
            ])
            second_answer = random_event([
                f"{winner_gender} дня - {self.bot.get_mention(winner_profile)}",
                f"НЕВЕРОЯТНО, НО {winner_gender} дня - {self.bot.get_mention(winner_profile)}",
                f"Сначала я не поверил, что {winner_gender} дня - {self.bot.get_mention(winner_profile)}, но куда деваться",
                f"Мда, и этот человек - {self.bot.get_mention(winner_profile)} сегодня {winner_gender} дня",
                f"И вот он, крем нашего пирожного — {self.bot.get_mention(winner_profile)}!",
                f"Аплодируем стоя: {winner_gender} дня — {self.bot.get_mention(winner_profile)}!",
                f"Игра окончена. Победитель — {self.bot.get_mention(winner_profile)}. Принимайте поздравления, {winner_gender} дня!",
                f"Кто здесь {winner_gender} дня? Правильно, {self.bot.get_mention(winner_profile)}!",
                f"Как в казино, только без денег. {winner_gender} дня — {self.bot.get_mention(winner_profile)}, поздравляем!",
                f"На волне случайности выносится вердикт: {winner_gender} дня — {self.bot.get_mention(winner_profile)}",
                f"Все путем, {self.bot.get_mention(winner_profile)}. Сегодня ты — звезда, {winner_gender} дня!",
                f"Забудьте о зодиаках, {winner_gender} дня здесь — {self.bot.get_mention(winner_profile)}",
                f"Собаки лают, караван идет, а {winner_gender} дня — {self.bot.get_mention(winner_profile)}",
                f"Расклад таков: {winner_gender} дня почетно присваивается {self.bot.get_mention(winner_profile)}. Ну что, парад готовим?",
                f"Ладно, примем как данность: {winner_gender} дня – это {self.bot.get_mention(winner_profile)}"
            ])

            return ResponseMessage([
                ResponseMessageItem(text=first_answer),
                ResponseMessageItem(text=second_answer)
            ])

    def _get_petrovich_gamers(self) -> QuerySet[PetrovichUser]:
        role_banned = Role.objects.get(name=RoleEnum.BANNED.name)
        gamers = PetrovichUser.objects \
            .filter(chat=self.event.chat, active=True) \
            .exclude(profile__roles=role_banned) \
            .filter(profile__chats=self.event.chat)
        return gamers
