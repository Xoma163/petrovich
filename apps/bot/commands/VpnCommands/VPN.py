import validators

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.consts.Exceptions import PWarning
from apps.service.models import Domain


class VPN(Command):
    name = "vpn"
    access = Role.VPN

    suggest_for_similar = False
    hidden = True

    def start(self):
        if self.event.message.args:
            arg0 = self.event.message.args[0]
        else:
            arg0 = None
        menu = [
            [['добавить', 'add'], self.add],
            [['default'], self.list]
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def add(self):
        self.check_args(2)
        url = self.event.message.args[1]
        if not validators.url(url):
            raise PWarning("Ссылка не валидна")
        if not url.startswith("https"):
            raise PWarning("Ссылка должна начинаться с https")
        try:
            Domain.objects.get(name=url)
            return "Такой домен уже есть"
        except Domain.DoesNotExist:
            Domain.objects.create(name=url)
            return "Добавил"

    def list(self):
        domains = Domain.objects.all()
        if not domains.exists():
            return "Доменов нет"
        domains_str = [x.name for x in domains]
        return "\n".join(domains_str)
