from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.management.commands.start import camera_handler


class Birds(CommonCommand):
    def __init__(self):
        names = ["с", "c", "синички"]
        help_text = "Синички - ссылка и гифка с синичками"
        detail_help_text = "Синички [кол-во кадров=20] - ссылка и гифка с синичками. Максимум 200 кадров"
        keyboard = [{'text': 'Синички 0', 'color': 'blue', 'row': 2, 'col': 1},
                    {'text': 'Синички 20', 'color': 'blue', 'row': 2, 'col': 2},
                    {'text': 'Синички 100', 'color': 'blue', 'row': 2, 'col': 3}]

        super().__init__(names, help_text, detail_help_text, keyboard, int_args=[0], access=Role.TRUSTED,
                         platforms=['vk', 'tg'])

    def start(self):
        self.bot.set_activity(self.event.peer_id)
        attachments = []
        try:
            image = camera_handler.get_img()
        except RuntimeError as e:
            print(e)
            raise RuntimeWarning("какая-то дичь с синичками. Зовите разраба")
        attachment = self.bot.upload_photos(image)[0]
        attachments.append(attachment)

        frames = 20
        if self.event.args:
            frames = self.event.args[0]
            self.check_number_arg_range(frames, 0, camera_handler.MAX_FRAMES)

        if frames != 0:
            try:
                document = camera_handler.get_gif(frames)
            except RuntimeError as e:
                return str(e)
            attachment = self.bot.upload_document(document, self.event.peer_id, "Синички")
            attachments.append(attachment)
        attachments.append('https://birds.xoma163.xyz')
        if len(attachments) == 2 or self.event.platform == 'vk ':
            return {
                'attachments': attachments,
                "keyboard": self.bot.get_inline_keyboard(self.names[0], args={"frames": frames}),
                'dont_parse_links': True
            }
        else:
            self.bot.send_message(self.event.peer_id, attachments=[attachments[0]])
            self.bot.send_message(self.event.peer_id, attachments=[attachments[1]])
            return None
