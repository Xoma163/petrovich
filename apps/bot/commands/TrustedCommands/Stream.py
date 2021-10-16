from urllib.parse import urlparse

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.consts.Exceptions import PWarning
from apps.service.models import Service


class Stream(Command):
    name = "стрим"
    help_text = "ссылка на стрим"
    help_texts = [
        "- ссылка на стрим"
        "[новая ссылка] - меняет ссылку на стрим. Требуются права модератора"
    ]
    access = Role.TRUSTED

    def start(self):
        if self.event.message.args is None:
            stream, _ = Service.objects.get_or_create(name="stream")
            stream_link = stream.value
            if len(stream_link) < 5:
                raise PWarning("Стрим пока не идёт")
            else:
                return {'msg': stream_link, 'attachments': [stream_link]}
        else:
            self.check_sender(Role.MODERATOR)

            if len(self.event.message.args[0]) >= 5 and not urlparse(self.event.message.args[0]).hostname:
                raise PWarning("Пришлите ссылку")
            Service.objects.update_or_create(name="stream", defaults={'value': self.event.message.args[0]})
            return "Ссылка изменена на " + self.event.message.args[0]
