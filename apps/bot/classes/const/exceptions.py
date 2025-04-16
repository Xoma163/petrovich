class PetrovichException(Exception):
    def __init__(self, msg=None, keyboard=None, reply_to=None):
        if keyboard is None:
            keyboard = {}
        self.msg = msg
        self.keyboard = keyboard
        self.reply_to = reply_to



class PSkip(PetrovichException):
    """
    Просто скипает выполнение
    """


class PSkipContinue(PSkip):
    """
    Просто скипает выполнение и переходит к обработке следующий команды
    """

class PIDK(PetrovichException):
    """
    Я не знаю команды
    """


class PWarning(PetrovichException):
    level = 'warning'


class PError(PetrovichException):
    level = 'error'


class PSubscribeIndexError(Exception):
    pass
