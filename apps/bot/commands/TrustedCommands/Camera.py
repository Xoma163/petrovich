from apps.bot.classes.Consts import Role, Platform
from apps.bot.classes.Exceptions import PWarning, PError
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.management.commands.start import camera_handler


class Camera(CommonCommand):
    name = "камера"
    names = ["с", "c"]
    help_text = "ссылка и гифка с камеры"
    help_texts = ["[кол-во кадров=20] - ссылка и гифка с камеры. Максимум 200 кадров"]
    int_args = [0]
    access = Role.TRUSTED
    platforms = [Platform.VK, Platform.TG]

    def start(self):
        self.bot.set_activity(self.event.peer_id)
        attachments = []
        try:
            image = camera_handler.get_img()
        except PWarning as e:
            print(e)
            raise PError("какая-то дичь с камерой. Зовите разраба")
        attachment = self.bot.upload_photos(image)[0]
        attachments.append(attachment)

        frames = 20
        if self.event.args:
            frames = self.event.args[0]
            self.check_number_arg_range(frames, 0, camera_handler.MAX_FRAMES)

        if frames != 0:
            try:
                document = camera_handler.get_gif(frames)
            except PError as e:
                return str(e)
            attachment = self.bot.upload_animation(document, self.event.peer_id, "Камера")
            attachments.append(attachment)
        attachments.append('https://birds.andrewsha.net')
        if len(attachments) == 2 or self.event.platform == Platform.VK:
            return {
                'attachments': attachments,
                "keyboard": self.bot.get_inline_keyboard(self.name, args={"frames": frames}),
                'dont_parse_links': True
            }
        else:
            self.bot.send_message(self.event.peer_id, attachments=[attachments[0]])
            self.bot.send_message(self.event.peer_id, attachments=[attachments[1]])
            return None
