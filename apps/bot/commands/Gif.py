from io import BytesIO

from PIL import Image

from apps.bot.classes.Command import Command
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment


class Gif(Command):
    name = "гиф"
    names = ["гифа", "gif"]

    help_text = "создаёт гифку из присланных картинок"
    help_texts = [
        "[пауза между картинками = 0.5] (Изображения/Пересылаемое сообщение с изображением) - создаёт гифку из картинок. Паузу можно указать в секундах от 0 до 2"
    ]
    enabled = False
    float_args = [0]

    def start(self):
        duration = 0.5
        if self.event.message.args:
            duration = self.event.message.args[0]
            self.check_number_arg_range(duration, 0, 2)

        images = self.event.get_all_attachments(PhotoAttachment)

        pil_images = []
        for image in images:
            image.download_content()
            pil_image = Image.open(BytesIO(image.content))
            pil_image.info['duration'] = duration
            pil_images.append(pil_image)

        gif = BytesIO()
        pil_images[0].save(
            gif,
            format="GIF",
            save_all=True,
            append_images=pil_images[1:],
            loop=0,
        )

        attachments = [self.bot.upload_video(gif, self.event.peer_id, "Гифа", filename="gifa.mp4")]
        return {
            'attachments': attachments,
        }
