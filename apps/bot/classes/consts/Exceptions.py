class PetrovichException(Exception):
    def __init__(self, msg=None, keyboard=None):
        if keyboard is None:
            keyboard = {}
        self.msg = msg
        self.keyboard = keyboard


class PSkip(PetrovichException):
    pass


class PIDK(PetrovichException):
    """
    I dont know commands
    """
    pass


class PWarning(PetrovichException):
    level = 'warning'


class PError(PetrovichException):
    level = 'error'
