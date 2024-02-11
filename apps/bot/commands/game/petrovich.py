import datetime
from threading import Lock

from django.contrib.auth.models import Group

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextItem, HelpText, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.utils.utils import localize_datetime, remove_tz, random_event
from apps.games.models import PetrovichGames, PetrovichUser
from petrovich.settings import DEFAULT_TIME_ZONE

lock = Lock()


class Petrovich(Command):
    name = "петрович"
    names = ['петровна']

    help_text = HelpText(
        commands_text="мини-игра, определяющая кто Петрович Дня",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand(None, "мини-игра, определяющая кто Петрович дня"),
                HelpTextItemCommand("рег", "регистрация в игре"),
                HelpTextItemCommand("дерег", "дерегистрация в игре")
            ])
        ]
    )

    conversation = True
    platforms = [Platform.TG]

    bot: TgBot

    def start(self) -> ResponseMessage:
        if self.event.message.args:
            arg0 = self.event.message.args[0]
        else:
            arg0 = None
        menu = [
            [['рег', 'регистрация'], self.menu_reg],
            [['дерег'], self.menu_dereg],
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

    def menu_dereg(self):
        p_user = PetrovichUser.objects.filter(profile=self.event.sender, chat=self.event.chat).first()
        if p_user is not None and p_user.active:
            p_user.active = False
            p_user.save()
            answer = "Ок"
        else:
            answer = "А ты и не зареган"
        return ResponseMessage(ResponseMessageItem(text=answer))

    def menu_play(self) -> ResponseMessage:
        with lock:
            datetime_now = localize_datetime(datetime.datetime.utcnow(), DEFAULT_TIME_ZONE)
            winner_today = PetrovichGames.objects.filter(chat=self.event.chat).first()
            if winner_today:
                datetime_last = localize_datetime(remove_tz(winner_today.date), DEFAULT_TIME_ZONE)
                if (datetime_now.date() - datetime_last.date()).days <= 0:
                    if winner_today.profile.gender and winner_today.profile.gender == '1':
                        winner_gender = "Петровна"
                    else:
                        winner_gender = "Петрович"
                    answer = f"{winner_gender} дня - {winner_today.profile}"
                    return ResponseMessage(ResponseMessageItem(text=answer))

            group_banned = Group.objects.get(name=Role.BANNED.name)
            winner = PetrovichUser.objects \
                .filter(chat=self.event.chat, active=True) \
                .exclude(profile__groups=group_banned) \
                .filter(profile__chats=self.event.chat) \
                .order_by("?") \
                .first()
            if winner:
                winner = winner.profile
            else:
                button = self.bot.get_button('Зарегистрироваться', self.name, ['рег'])
                keyboard = self.bot.get_inline_keyboard([button])
                raise PWarning(
                    f"Нет участников игры. Зарегистрируйтесь! {self.bot.get_formatted_text_line('/петрович рег')}",
                    keyboard=keyboard
                )

            winner_petrovich = PetrovichGames(profile=winner, chat=self.event.chat)
            winner_petrovich.save()

            winner_gender = "Петровна" if winner.is_female else "Петрович"

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
                f"{winner_gender} дня - {self.bot.get_mention(winner)}",
                f"НЕВЕРОЯТНО, НО {winner_gender} дня - {self.bot.get_mention(winner)}",
                f"Сначала я не поверил, что {winner_gender} дня - {self.bot.get_mention(winner)}, но куда деваться",
                f"Мда, и этот человек - {self.bot.get_mention(winner)} сегодня {winner_gender} дня",
                f"И вот он, крем нашего пирожного — {self.bot.get_mention(winner)}!",
                f"Аплодируем стоя: {winner_gender} дня — {self.bot.get_mention(winner)}!",
                f"Игра окончена. Победитель — {self.bot.get_mention(winner)}. Принимайте поздравления, {winner_gender} дня!",
                f"Кто здесь {winner_gender} дня? Правильно, {self.bot.get_mention(winner)}!",
                f"Как в казино, только без денег. {winner_gender} дня — {self.bot.get_mention(winner)}, поздравляем!",
                f"На волне случайности выносится вердикт: {winner_gender} дня — {self.bot.get_mention(winner)}",
                f"Все путем, {self.bot.get_mention(winner)}. Сегодня ты — звезда, {winner_gender} дня!",
                f"Забудьте о зодиаках, {winner_gender} дня здесь — {self.bot.get_mention(winner)}",
                f"Собаки лают, караван идет, а {winner_gender} дня — {self.bot.get_mention(winner)}",
                f"Расклад таков: {winner_gender} дня почетно присваивается {self.bot.get_mention(winner)}. Ну что, парад готовим?",
                f"Ладно, примем как данность: {winner_gender} дня – это {self.bot.get_mention(winner)}"
            ])

            return ResponseMessage([
                ResponseMessageItem(text=first_answer),
                ResponseMessageItem(text=second_answer)
            ])
