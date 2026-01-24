class NothingLogger(object):
    """
    Класс для отключения логов
    """

    @staticmethod
    def debug(msg):
        """
        Не логировать debug
        """

    @staticmethod
    def warning(msg):
        """
        Не логировать warning
        """

    @staticmethod
    def error(msg):
        """
        Не логировать error
        """
