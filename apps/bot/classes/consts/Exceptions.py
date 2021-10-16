class PSkip(Exception):
    pass


class PWarning(Exception):
    level = 'warning'


class PError(Exception):
    level = 'error'
