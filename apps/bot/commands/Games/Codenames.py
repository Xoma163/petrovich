import json
import random
from threading import Lock

from apps.bot.classes.Consts import Role, Platform
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.games.models import CodenamesUser, CodenamesSession, Gamer
from petrovich.settings import STATIC_ROOT

lock = Lock()

MIN_USERS = 4
DIMENSION = 5

WORDS = ['Австралия', 'Автомат', 'Агент', 'Адвокат', 'Азия', 'Акт', 'Альбом', 'Альпы', 'Америка', 'Амфибия', 'Ангел',
         'Англия', 'Антарктида', 'Аппарат', 'Атлантида', 'Африка', 'Ацтек', 'Бабочка', 'База', 'Байкал', 'Банк', 'Баня',
         'Бар', 'Барьер', 'Бассейн', 'Батарея', 'Башня', 'Берёза', 'Берлин', 'Бермуды', 'Билет', 'Биржа', 'Блин',
         'Блок', 'Боевик', 'Бокс', 'Болезнь', 'Больница', 'Бомба', 'Боров', 'Борт', 'Ботинок', 'Бочка', 'Брак',
         'Бревно', 'Бумага', 'Бутылка', 'Бык', 'Вагон', 'Вал', 'Ведьма', 'Век', 'Венец', 'Вертолёт', 'Верфь', 'Вес',
         'Ветер', 'Взгляд', 'Вид', 'Вилка', 'Вирус', 'Вода', 'Водолаз', 'Вождь', 'Воздух', 'Война', 'Волна', 'Вор',
         'Время', 'Высота', 'Газ', 'Галоп', 'Гвоздь', 'Гений', 'Германия', 'Гигант', 'Глаз', 'Голливуд', 'Голова',
         'Горло', 'Горн', 'Гранат', 'Гребень', 'Греция', 'Гриф', 'Груша', 'Дама', 'Декрет', 'День', 'Десна', 'Динозавр',
         'Диск', 'Доктор', 'Дракон', 'Дробь', 'Дума', 'Дух', 'Дыра', 'Дятел', 'Европа', 'Египет', 'Единорог', 'Ёрш',
         'Жизнь', 'Жила', 'Жук', 'Журавль', 'Залог', 'Замок', 'Заноза', 'Запад', 'Запах', 'Заяц', 'Звезда', 'Зебра',
         'Земля', 'Знак', 'Золото', 'Зона', 'Зуб', 'Игла', 'Игра', 'Икра', 'Индия', 'Институт', 'Кабинет', 'Кавалер',
         'Кадр', 'Казино', 'Камень', 'Камера', 'Канал', 'Караул', 'Карлик', 'Карта', 'Каша', 'Кенгуру', 'Кентавр',
         'Кетчуп', 'Киви', 'Кисть', 'Кит', 'Китай', 'Клетка', 'Ключ', 'Кокетка', 'Кол', 'Колода', 'Колонна', 'Кольцо',
         'Команда', 'Конёк', 'Контрабандист', 'Концерт', 'Кора', 'Корабль', 'Королева', 'Король', 'Корона', 'Коса',
         'Кость', 'Косяк', 'Кошка', 'Край', 'Кран', 'Крест', 'Кролик', 'Крошка', 'Круг', 'Крыло', 'Кулак', 'Курс',
         'Лад', 'Лазер', 'Лама', 'Ласка', 'Лев', 'Лёд', 'Лейка', 'Лес', 'Лимузин', 'Линия', 'Липа', 'Лист', 'Лицо',
         'Ложе', 'Лондон', 'Лошадь', 'Лук', 'Луна', 'Луч', 'Масло', 'Масса', 'Мат', 'Машина', 'Мёд', 'Медведь',
         'Мексика', 'Мелочь', 'Место', 'Механизм', 'Микроскоп', 'Миллионер', 'Мир', 'Морковь', 'Мороженое', 'Москва',
         'Мост', 'Мотив', 'Мушка', 'Мышь', 'Налёт', 'Наряд', 'Небоскрёб', 'Ниндзя', 'Нож', 'Номер', 'Норка', 'Нота',
         'Ночь', 'Нью-йорк', 'Няня', 'Область', 'Облом', 'Образ', 'Образование', 'Обрез', 'Овсянка', 'Огонь', 'Олимп',
         'Опера', 'Операция', 'Орган', 'Орёл', 'Осьминог', 'Отель', 'Падение', 'Палата', 'Палец', 'Палочка', 'Панель',
         'Пара', 'Парашют', 'Парк', 'Партия', 'Пассаж', 'Паук', 'Пачка', 'Пекин', 'Перевод', 'Перемена', 'Перо',
         'Перчатка', 'Пилот', 'Пингвин', 'Пирамида', 'Пират', 'Пистолет', 'Плата', 'Платье', 'Площадь', 'Пляж', 'Побег',
         'Повар', 'Подкова', 'Подъём', 'Покров', 'Пол', 'Поле', 'Полис', 'Полиция', 'Помёт', 'Порода', 'Посольство',
         'Поток', 'Почка', 'Пояс', 'Право', 'Предложение', 'Предприниматель', 'Прибор', 'Привод', 'Призрак',
         'Принцесса', 'Пришелец', 'Пробка', 'Проводник', 'Проказа', 'Прокат', 'Проспект', 'Профиль', 'Путь', 'Пушкин',
         'Развод', 'Разворот', 'Рак', 'Раковина', 'Раствор', 'Рейд', 'Рим', 'Робот', 'Рог', 'Род', 'Рок', 'Рубашка',
         'Рукав', 'Рулетка', 'Рыба', 'Рысь', 'Рыцарь', 'Салют', 'Сантехник', 'Сатурн', 'Свет', 'Свидетель', 'Секрет',
         'Секция', 'Сердце', 'Сеть', 'Сила', 'Скат', 'Смерть', 'Снаряд', 'Снег', 'Снеговик', 'Собака', 'Совет',
         'Солдат', 'Соль', 'Состав', 'Спутник', 'Среда', 'Ссылка', 'Стадион', 'Стан', 'Станок', 'Ствол', 'Стекло',
         'Стена', 'Стойка', 'Стол', 'Стопа', 'Стрела', 'Строй', 'Струна', 'Стул', 'Ступень', 'Судьба', 'Супергерой',
         'Такса', 'Танец', 'Тарелка', 'Театр', 'Телескоп', 'Течение', 'Титан', 'Токио', 'Точка', 'Трава', 'Треугольник',
         'Труба', 'Туба', 'Тур', 'Ударник', 'Удел', 'Узел', 'Урал', 'Урна', 'Утка', 'Утконос', 'Учёный', 'Учитель',
         'Факел', 'Фаланга', 'Фига', 'Флейта', 'Фокус', 'Форма', 'Франция', 'Хвост', 'Хлопок', 'Центр', 'Церковь',
         'Частица', 'Червь', 'Шар', 'Шоколад', 'Шпагат', 'Шпион', 'Штат', 'Шуба', 'Экран', 'Эльф', 'Эфир', 'Юпитер',
         'Яблоко', 'Яд', 'Язык', 'Якорь', 'Ясли']

translator = {
    'red': 'красная команда',
    'blue': 'синяя команда',
    'red_wait': 'капитан красной команды',
    'blue_wait': 'капитан синей команы',
}

translator_commands = {
    'red': 'красной',
    'blue': 'синей'
}

translator_role = {
    'captain': "Капитан",
    'player': "Игрок"
}


def check_player_captain(player):
    if player.role == 'captain':
        return True
    raise RuntimeWarning("Загадывать может только капитан")


def check_next_step(session, step_name):
    if session.next_step == step_name:
        return True

    raise RuntimeWarning("Сейчас не ваш ход")


def check_player(player):
    if player:
        return True
    raise RuntimeWarning("Вы не игрок")


def check_session(session):
    if session:
        return True
    raise RuntimeWarning("Игра ещё не началась")


def check_not_session(session):
    if not session:
        return True
    raise RuntimeWarning("Игра уже началась")


def get_another_command(command):
    if command == 'red':
        return 'blue'
    elif command == 'blue':
        return 'red'


def get_str_players(players):
    codenames_users_list = []
    for player in players:
        if player.role_preference:
            codenames_users_list.append(f"{str(player.user)} ({translator_role[player.role_preference]})")
        else:
            codenames_users_list.append(f"{str(player.user)}")
    return "\n".join(codenames_users_list)


# ToDo: TG клавы
class Codenames(CommonCommand):
    def __init__(self):
        names = ["коднеймс", "кн"]
        help_text = "Коднеймс - игра коднеймс"
        detail_help_text = "Коднеймс - игра коднеймс\n" \
                           "Коднеймс правила - правила игры\n" \
                           "Коднеймс рег [роль=рандом] - регистрация в игре. Роли: капитан, игрок\n" \
                           "Коднеймс дерег - дерегистрация в игре\n" \
                           "Коднеймс старт - старт игры\n" \
                           "Коднеймс клава - текущая клавиатура игры\n" \
                           "Коднеймс инфо - команды, кол-во слов, чей ход, загаданное слово\n" \
                           "Коднеймс загадать (кол-во слов) (слово) \n" \
                           "Коднеймс слово (слово) - выбрать слово. Либо тык в клаву\n" \
                           "Коднеймс фиксклавы - рекомендации для фикса стилей клавиатуры\n" \
                           "Коднеймс удалить - удаляет сессию игры. Только для админа конфы\n\n" \
                           "Небольшая информация для тех, кто хочет поиграть в коднеймс без урезания слов на " \
                           "клавиатурах контактом. Как я выяснил, с мобилок официальный клиент урезает клавиатуру. " \
                           "Нормально отображаёт её только Kate Mobile и вроде бы VK Coffee. Для ПК дела получше, " \
                           "слов умещается больше, но всё равно некоторые урезаются. Для того, чтобы этого избежать " \
                           "можно поправить стили контакта, чтобы они не урезали почти половину полезного места. Для " \
                           "этого я сделал отдельную инструкцию, которую можно получить по команде /кн фиксклавы"
        super().__init__(names, help_text, detail_help_text, platforms=[Platform.VK], args=1)

    def init_var(self):

        if self.event.from_chat:
            self.session = CodenamesSession.objects.filter(chat=self.event.chat).first()
            self.players = CodenamesUser.objects.filter(chat=self.event.chat)
            self.player = self.players.filter(user=self.event.sender).first()
            self.players_captains = self.players.filter(role='captain')
        elif self.event.from_user:
            self.player = CodenamesUser.objects.filter(user=self.event.sender).first()
            chat = self.player.chat
            self.session = CodenamesSession.objects.filter(chat=chat).first()
            self.players = CodenamesUser.objects.filter(chat=chat)
            self.players_captains = self.players.filter(role='captain')

    def start(self):
        with lock:
            self.init_var()

            if self.event.payload:
                return self.menu_word()

            arg0 = self.event.args[0].lower()
            menu = [
                [['рег', 'регистрация'], self.menu_reg],
                [['правила'], self.menu_rules],
                [['дерег'], self.menu_dereg],
                [['старт'], self.menu_start],
                [['загадать'], self.menu_makeup],
                [['слово'], self.menu_word],
                [['клава'], self.menu_keyboard],
                [['инфо', 'инфа', 'информация'], self.menu_info],
                [['удалить'], self.menu_delete],
                [['фикс', 'фиксклавы'], self.menu_fix_keyboard]
            ]
            method = self.handle_menu(menu, arg0)
            return method()

    # START MENU
    def menu_reg(self):
        if len(Gamer.objects.filter(user=self.event.sender)) == 0:
            Gamer(user=self.event.sender).save()

        self.check_conversation()
        if len(CodenamesUser.objects.filter(chat=self.event.chat, user=self.event.sender)) > 0:
            raise RuntimeWarning('Ты уже зарегистрирован')
        if len(CodenamesUser.objects.filter(user=self.event.sender)) > 0:
            raise RuntimeWarning('Нельзя участвовать сразу в двух играх')

        role_preference = None
        if len(self.event.args) >= 2:
            if self.event.args[1].lower() in ["кэп", "капитан"]:
                role_preference = "captain"
            elif self.event.args[1].lower() in ["игрок"]:
                role_preference = "player"
            else:
                raise RuntimeWarning("Не знаю такой роли для регистрации")

        codenames_user = CodenamesUser(user=self.event.sender,
                                       chat=self.event.chat,
                                       role_preference=role_preference)
        if not self.session:
            codenames_user.save()
            return "Зарегистрировал. Сейчас зарегистрированы:\n" \
                   f"{get_str_players(self.players)}\n"
        else:
            if len(self.players) % 2 == 0:
                codenames_user.command = 'blue'
            else:
                codenames_user.command = 'red'
            codenames_user.save()
            return f"Зарегистрировал. Ты в {translator_commands[codenames_user.command]} команде"

    def menu_rules(self):
        attachment = self.bot.get_attachment_by_id('doc', None, '550553057')
        return {'attachments': attachment}

    def menu_dereg(self):

        self.check_conversation()
        check_not_session(self.session)
        self.player.delete()
        return "Дерегнул. Сейчас зарегистрированы:\n" \
               f"{get_str_players(self.players)}\n"

    def menu_start(self):

        self.check_conversation()
        check_not_session(self.session)
        if len(self.players) < MIN_USERS:
            return f"Минимальное количество игроков - {MIN_USERS}. Сейчас зарегистрированы:\n" \
                   f"{get_str_players(self.players)}\n"
        return self.prepare_game()

    def menu_makeup(self):
        check_session(self.session)
        check_player(self.player)
        self.check_pm()
        check_player_captain(self.player)
        command = self.player.command
        check_next_step(self.session, command + "_wait")
        if len(self.event.args) < 3:
            raise RuntimeWarning("Недостаточно аргументов")
        self.int_args = [1]
        try:
            self.parse_int()
            count = self.event.args[1]
            word = self.event.args[2]
        except RuntimeWarning:
            self.int_args = [2]
            self.parse_int()
            word = self.event.args[1]
            count = self.event.args[2]

        if count > 9:
            count = 9
        elif count < 1:
            raise RuntimeWarning("Число загадываемых слов не может быть меньше 1")

        self.do_the_riddle(command, count, word)
        return 'Отправил в конфу'

    def menu_word(self):
        self.check_conversation()
        check_session(self.session)
        check_player(self.player)
        if self.player.role == 'captain':
            raise RuntimeWarning("Капитан не может угадывать")
        check_next_step(self.session, self.player.command)
        if self.event.payload:
            if self.event.payload['args']['action'] in ['слово']:
                return self.select_word(self.event.payload['args']['row'],
                                        self.event.payload['args']['col'])
            raise RuntimeError("Внутренняя ошибка. Неизвестный action в payload")
        elif self.event.args[0].lower() in ['слово']:
            self.check_args(2)
            word = self.event.args[1].capitalize()
            board = self.session.board

            find_row = None
            find_col = None
            for i, row in enumerate(board):
                if find_row is not None:
                    break
                for j, elem in enumerate(row):
                    if elem['name'] == word:
                        find_row = i
                        find_col = j
                        if elem['state'] == 'open':
                            raise RuntimeWarning("Слово уже открыто")
                        break
            self.select_word(find_row, find_col)
            return

    def menu_keyboard(self):
        check_session(self.session)
        check_player(self.player)
        board = self.session.board
        user_is_captain = self.player.role == 'captain'
        if user_is_captain:
            if self.event.from_chat:
                self.send_keyboard(board)
            else:
                self.check_pm()
                self.send_captain_keyboard(board)
        else:
            self.check_conversation()
            self.send_keyboard(board)
        return

    def menu_info(self):
        self.check_conversation()
        if self.session:
            msg = self.get_info()
            return msg
        else:
            return "Сейчас зарегистрированы:\n" \
                   f"{get_str_players(self.players)}\n"

    def menu_delete(self):
        self.check_sender(Role.CONFERENCE_ADMIN)
        if self.session is None:
            raise RuntimeWarning("Нечего удалять")
        else:
            self.session.delete()
            return "Удалил"

    def menu_fix_keyboard(self):
        msg = "1) Устанавливаем stylish (" \
              "https://chrome.google.com/webstore/detail/stylish-custom-themes-for/fjnbnpbmkenffdnngjfgmeleoegfcffe?hl=ru)\n" \
              "2) Создаём свой стиль\n" \
              "3) Копируем туда следующий код:\n\n" \
              ".Button--size-m:not(.Button--link) {\n" \
              "padding:0 !important;\n" \
              "}\n" \
              ".Button--overflow {\n" \
              "overflow: visible !important;\n" \
              "}\n" \
              ".BotButtonLabel{\n" \
              "max-width:100%\n" \
              "}\n\n" \
              "4) Сохраняем\n" \
              "5) Обновляем страницу с перезагрузкой кэша (Ctrl+F5)\n" \
              "6) Ура! Теперь клава будет нормально выводиться у всех ботов"
        attachment = self.bot.upload_photos(f"{STATIC_ROOT}/bot/img/fix_keyboard.jpg")
        return {'msg': msg, 'attachments': attachment}

    # END MENU

    # Подготовка и старт игры
    def prepare_game(self):
        def get_random_words():
            words_shuffled = sorted(WORDS, key=lambda x: random.random())[:DIMENSION * DIMENSION]
            team_words_shuffled = []
            for i, word in enumerate(words_shuffled):
                team_words_shuffled.append(
                    {'state': 'close', 'name': word})
                if i < 9:
                    team_words_shuffled[-1]['type'] = 'blue'
                elif i == 9:
                    team_words_shuffled[-1]['type'] = 'death'
                elif i < 18:
                    team_words_shuffled[-1]['type'] = 'red'
                else:
                    team_words_shuffled[-1]['type'] = 'neutral'

            team_words_shuffled = sorted(team_words_shuffled, key=lambda x: random.random())
            for i, word in enumerate(team_words_shuffled):
                team_words_shuffled[i]['row'] = int(i / DIMENSION)
                team_words_shuffled[i]['col'] = i % DIMENSION
            words_table = []
            for i in range(DIMENSION):
                words_table.append(team_words_shuffled[i * DIMENSION:(i + 1) * DIMENSION])

            return words_table

        preference_captain = self.players.filter(role_preference='captain')

        if len(preference_captain) < 2:
            preference_none = self.players.filter(role_preference=None).order_by('?')[:(2 - len(preference_captain))]
            captains = preference_captain | preference_none
        else:
            captains = preference_captain.order_by('?')[:2]

        if len(captains) < 2:
            raise RuntimeWarning("Недостаточно игроков на роль капитана")

        for captain in captains:
            captain.role = 'captain'

        players = self.players.exclude(id__in=[captain.id for captain in captains])
        for player in players:
            player.role = 'player'

        players = sorted(players, key=lambda x: random.random())
        self.players = CodenamesUser.objects.filter(chat=self.event.chat)
        half_users = int(len(players) / 2)
        if len(players) % 2 == 1:
            half_users += 1

        commands = {'blue': [], 'red': []}
        commands['blue'].append(captains[0])
        commands['red'].append(captains[1])
        commands['blue'] += players[:half_users]
        commands['red'] += players[half_users:]

        for command in commands:
            for user in commands[command]:
                user.command = command
                user.save()

        board = get_random_words()
        session = CodenamesSession()
        session.chat = self.event.chat
        session.board = board
        session.save()
        self.session = session

        self.bot.send_message(self.event.peer_id, msg=self.get_info(), keyboard=self.get_keyboard(board))

        for captain in captains:
            self.send_captain_keyboard(board, captain,
                                       msg=f"Вы капитан {translator_commands[captain.command]} команды")

    # Тык игрока
    def select_word(self, row, col):
        board = self.session.board
        if board[row][col]['state'] == 'open':
            raise RuntimeWarning("Слово уже открыто")

        command = self.player.command
        another_command = get_another_command(command)
        selected_word = board[row][col]
        selected_word['state'] = 'open'
        self.session.board = board

        if selected_word['type'] == command:
            self.session.count -= 1
            if self.session.count == 0:
                self.session.next_step = f"{another_command}_wait"
                self.bot.send_message(self.session.chat.chat_id,
                                      f"Угадали!\nПередаём ход капитану {translator_commands[another_command]} "
                                      "команды",
                                      keyboard=self.get_keyboard(board))
                for captain in self.players_captains:
                    self.send_captain_keyboard(board, captain)
            else:
                self.bot.send_message(self.session.chat.chat_id,
                                      "Угадали!\nПродолжайте угадывать",
                                      keyboard=self.get_keyboard(board))
            self.session.save()
        elif selected_word['type'] == another_command or selected_word['type'] == 'neutral':
            self.session.next_step = f"{another_command}_wait"
            self.session.save()

            self.bot.send_message(self.session.chat.chat_id,
                                  f"Не угадали :(\nПередаём ход капитану {translator_commands[another_command]} команды",
                                  keyboard=self.get_keyboard(board))
            for captain in self.players_captains:
                self.send_captain_keyboard(board, captain)
        elif selected_word['type'] == 'death':
            self.bot.send_message(self.session.chat.chat_id, "Смэрт")
            self.game_over(another_command, board)
            return

        is_game_over = self.check_game_over(board)
        if is_game_over:
            self.game_over(is_game_over, board)
            return

    # Загадка капитана
    def do_the_riddle(self, command, count, word):

        self.bot.send_message(self.session.chat.chat_id,
                              f"Капитан {translator_commands[command]} команды:\n{count} - {word}")

        self.session.next_step = command
        self.session.count = count
        self.session.word = word
        self.session.save()

        board = self.session.board
        return {"msg": "Лови клаву", "keyboard": self.get_keyboard(board)}

    # Метод получает количество оставшихся закрытых слов команд
    @staticmethod
    def get_team_words(board):
        words = {'red': 0, 'blue': 0}
        for row in board:
            for elem in row:
                if elem['state'] == 'close':
                    if elem['type'] == 'red' or elem['type'] == 'blue':
                        words[elem['type']] += 1
        return words

    # Проверка на конец игры
    def check_game_over(self, board):
        team_words = self.get_team_words(board)

        if team_words['red'] == 0:
            return 'red'
        elif team_words['blue'] == 0:
            return 'blue'
        else:
            return None

    # Конец игры
    def game_over(self, winner, board):
        keyboard = self.get_keyboard(board, for_captain=True, game_over=True)
        self.bot.send_message(self.session.chat.chat_id,
                              f'Игра закончена.\nПобеда {translator_commands[winner]} команды',
                              keyboard=keyboard)

        for captain in self.players_captains:
            from apps.bot.initial import EMPTY_KEYBOARD
            self.bot.send_message(captain.user.user_id,
                                  "Игра закончена",
                                  keyboard=EMPTY_KEYBOARD)

        winners = self.players.filter(command=winner)
        for winner in winners:
            gamer = Gamer.objects.get(user=winner.user)
            gamer.codenames_points += 1
            gamer.save()

        self.session.delete()
        self.players.delete()

    def get_info(self):
        def get_teams():
            def get_command_msg(command_name, command_players):
                team_msg = f"{translator[command_name].capitalize()}:\n"
                for _player in command_players:
                    if _player.role == 'captain':
                        team_msg += f'{_player} - Капитан\n'
                    else:
                        team_msg += f'{_player}\n'
                return team_msg + "\n\n"

            _commands = {'red': [], 'blue': []}
            commands_msg = {'red': None, 'blue': None}
            for player in self.players:
                _commands[player.command].append(player)
            for _command in _commands:
                commands_msg[_command] = get_command_msg(_command, _commands[_command])

            return commands_msg

        commands_colors = ['blue', 'red']

        commands = get_teams()

        board = self.session.board
        words_left = self.get_team_words(board)

        riddle = None
        if self.session.next_step == 'red' or self.session.next_step == 'blue':
            riddle = f"{translator[self.session.next_step + '_wait'].capitalize()}:\n" \
                     f"{self.session.count} - {self.session.word}\n"
        step = f'Сейчас ходит {translator[self.session.next_step]}'

        spacer = "-----------------------------------------------------------"
        total_msg = ""
        for command in commands_colors:
            total_msg += f"{commands[command]}\n" \
                         f"Осталось слов - {words_left[command]}\n{spacer}\n"
        total_msg += step + f"\n{spacer}\n"
        if riddle:
            total_msg += riddle
        return total_msg

    # Работа с клавиатурами
    @staticmethod
    # Врап элемента клавиатуры
    def get_elem(elem, for_captain=False, game_over=False):
        def get_color():
            if for_captain:
                captain_color_translate = {
                    'red': 'negative',
                    'death': 'positive',
                    'blue': 'primary',
                    'neutral': 'secondary'
                }
                return captain_color_translate[elem['type']]
            else:
                color_translate = {'close': {
                    'red': 'secondary',
                    'death': 'secondary',
                    'blue': 'secondary',
                    'neutral': 'secondary'
                },
                    'open': {
                        'red': 'negative',
                        'death': 'positive',
                        'blue': 'primary',
                        'neutral': 'secondary'
                    }
                }
                return color_translate[elem['state']][elem['type']]

        def get_name():
            if game_over:
                return elem['name']
            else:
                name_translate = {
                    'open': "".join(["ᅠ" for _ in range(2)]),
                    'close': elem['name']
                }
                return name_translate[elem['state']]

        return {
            "action": {
                "type": "text",
                "label": get_name(),
                "payload": json.dumps({
                    "command": "коднеймс",
                    "args": {
                        "action": 'слово',
                        'row': elem['row'],
                        "col": elem['col'],
                        "state": elem['state']
                    }},
                    ensure_ascii=False)
            },
            "color": get_color()
        }

    # Обычная клава
    def get_keyboard(self, table, for_captain=False, game_over=False):
        buttons = []
        for row in table:
            rows = []
            for elem in row:
                rows.append(self.get_elem(elem, for_captain, game_over))
            buttons.append(rows)

        keyboard = {
            "one_time": False,
            "buttons": buttons,
        }
        return keyboard

    def send_keyboard(self, board):
        keyboard = self.get_keyboard(board)
        self.bot.send_message(self.session.chat.chat_id, msg="Лови клаву", keyboard=keyboard)

    def send_captain_keyboard(self, board, captain=None, msg="Лови клаву"):
        if captain:
            peer_id = captain.user.user_id
        else:
            peer_id = self.event.peer_id

        keyboard = self.get_keyboard(board, for_captain=True)
        self.bot.send_message(peer_id, msg=msg, keyboard=keyboard)
