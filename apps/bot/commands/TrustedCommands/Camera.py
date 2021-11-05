from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.management.commands.start import camera_handler


class Camera(Command):
    name = "камера"
    name_tg = 'camera'

    help_text = "ссылка и гифка с камеры"
    help_texts = ["[кол-во кадров=100] - ссылка и гифка с камеры. Максимум 1000 кадров"]

    int_args = [0]
    access = Role.TRUSTED
    platforms = [Platform.VK, Platform.TG]

    def start(self):
        frames = 100
        if self.event.message.args:
            frames = self.event.message.args[0]
            self.check_number_arg_range(frames, 0, camera_handler.MAX_FRAMES)

        if frames == 0:
            image = camera_handler.get_img()
            attachments = self.bot.upload_photos(image, peer_id=self.event.peer_id)
        else:
            document = camera_handler.get_gif(frames)
            attachments = [self.bot.upload_video(document, self.event.peer_id, "Камера", filename="camera.gif")]
        return {
            'attachments': attachments,
            "keyboard": self.bot.get_inline_keyboard(
                [{'command': self.name, 'button_text': "Ещё", 'args': [frames]}]
            )
        }
