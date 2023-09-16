class BotResponse:
    """
    Результат отправки ResponseMessageItem
    """

    def __init__(self, success: bool, response: dict):
        self.success: bool = success
        self.response: dict = response
