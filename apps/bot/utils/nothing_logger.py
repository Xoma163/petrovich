class NothingLogger(object):
    """
    Класс для отключения логов
    """

    @staticmethod
    def debug(msg):
        pass

    @staticmethod
    def warning(msg):
        pass

    @staticmethod
    def error(msg):
        pass
