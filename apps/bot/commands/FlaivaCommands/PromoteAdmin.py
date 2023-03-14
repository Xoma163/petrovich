from apps.bot.classes.consts.Consts import Platform, Role
from apps.bot.commands.MraziCommands.Nostalgia import Nostalgia


class PromoteAdmin(Nostalgia):
    name = "promote"
    access = Role.FLAIVA
    platforms = [Platform.TG]
    conversation = True

    def start(self):
        name = self.event.message.args[0]
        profile = self.bot.get_profile_by_name(name, self.event.chat)
        user_id = profile.get_user_by_platform(Platform.TG).user_id
        self.bot.promote_chat_member(self.event.chat.chat_id, user_id)
        return "done"
