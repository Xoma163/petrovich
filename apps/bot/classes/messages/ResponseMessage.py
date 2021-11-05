from copy import copy


class ResponseMessage:
    def __init__(self, msgs, peer_id):
        self.messages = []

        if isinstance(msgs, list):
            for item in msgs:
                rmi = ResponseMessageItem(item, peer_id)
                self.messages.append(rmi)
        else:
            self.messages = [ResponseMessageItem(msgs, peer_id)] if msgs else []

    def to_log(self) -> dict:
        """
        Вывод в логи
        """
        dict_self = copy(self.__dict__)
        dict_self['messages'] = [x.to_log() for x in dict_self['messages']]
        return dict_self

    def to_api(self) -> dict:
        """
        Вывод в API
        """
        dict_self = copy(self.__dict__)
        dict_self['messages'] = [x.to_api() for x in dict_self['messages']]

        return dict_self


class ResponseMessageItem:
    def __init__(self, msg, peer_id):
        if isinstance(msg, str) or isinstance(msg, int) or isinstance(msg, float):
            msg = {'text': str(msg)}

        msg_copy = copy(msg)

        self.peer_id = peer_id
        self.text = msg_copy.pop('text', "")
        self.attachments = msg_copy.pop('attachments', [])
        if not isinstance(self.attachments, list):
            self.attachments = [self.attachments]
        self.keyboard = msg_copy.pop('keyboard', {})
        self.kwargs = msg_copy

    def to_log(self) -> dict:
        """
        Вывод в логи
        """
        dict_self = copy(self.__dict__)
        dict_self['attachments'] = [x.to_log() for x in dict_self['attachments']]
        return dict_self

    def to_api(self) -> dict:
        """
        Вывод в API
        """
        dict_self = copy(self.__dict__)
        dict_self['attachments'] = [x.to_api() for x in dict_self['attachments']]
        del dict_self['peer_id']

        return dict_self
