class PetrovichException(Exception):
    def __init__(self, msg=None, keyboard=None):
        if keyboard is None:
            keyboard = {}
        self.msg = msg
        self.keyboard = keyboard


class PSkip(PetrovichException):
    """
    Просто скипает выполнение
    """


class PIDK(PetrovichException):
    """
    Я не знаю команды
    """


class PWarning(PetrovichException):
    level = 'warning'


class PError(PetrovichException):
    level = 'error'
