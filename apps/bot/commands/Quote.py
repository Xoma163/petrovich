import os
import textwrap
from io import BytesIO

from PIL import ImageFont, Image, ImageDraw, ImageFilter

from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_image_size_by_text
from petrovich.settings import STATIC_DIR

WIDTH = 620
BACKGROUND_COLOR = "#F5F5F5"


class Quote(CommonCommand):
    names = ["цитата", "(c)", "(с)"]
    help_text = "Цитата - сохраняет в цитатник сообщения"
    detail_help_text = "Цитата (Пересылаемые сообщение) - сохраняет в цитатник сообщения"
    fwd = True
    platforms = [Platform.VK]

    def start(self):
        msgs = []
        for msg in self.event.fwd:
            text = msg['text']
            if msg['from_id'] > 0:
                quote_user = self.bot.get_user_by_id(msg['from_id'])
                username = str(quote_user)
                avatar = quote_user.avatar
            else:
                quote_bot = self.bot.get_bot_by_id(msg['from_id'])
                username = str(quote_bot)
                avatar = quote_bot.avatar

            msgs.append({'username': username, 'text': text, 'avatar': avatar})
        pil_image = self.build_quote_image(msgs)
        bytes_io = BytesIO()
        pil_image.save(bytes_io, format='PNG')
        attachments = self.bot.upload_photos(bytes_io)
        return {"attachments": attachments}

    def get_centered_rounded_image(self, image: Image, max_size=80):
        w, h = image.size
        center_point = (w // 2, h // 2)
        min_size = min(center_point)
        cropped_image = image.crop((center_point[0] - min_size,
                                    center_point[1] - min_size,
                                    center_point[0] + min_size,
                                    center_point[1] + min_size))

        blur_radius = 0
        offset = 4
        back_color = Image.new(cropped_image.mode, cropped_image.size, BACKGROUND_COLOR)
        offset = blur_radius * 2 + offset
        mask = Image.new("RGBA", cropped_image.size, 255)

        draw = ImageDraw.Draw(mask)
        draw.ellipse((offset, offset, cropped_image.size[0] - offset, cropped_image.size[1] - offset),
                     fill=(255, 255, 255))
        mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))
        img_round = Image.composite(cropped_image, back_color, mask)

        img_round.thumbnail((max_size, max_size), Image.ANTIALIAS)
        return img_round

    @staticmethod
    def _image_concatenation(images: list):
        if len(images) == 0:
            return []
        if len(images) == 1:
            return images[0]
        total_height = sum([image.height for image in images])
        dst = Image.new('RGB', (images[0].width, total_height))

        dy = 0
        for image in images:
            dst.paste(image, (0, dy))
            dy += image.height
        return dst

    def _get_header(self):
        fontsize = 12
        margin_left = 70
        margin_top = 40
        line_width = 216
        text_color = "#333333"
        text = "Сохры"
        font = ImageFont.truetype(os.path.join(STATIC_DIR, 'fonts/Alegreya-Regular.ttf'), fontsize, encoding="unic")
        width, height = get_image_size_by_text(text, font)
        img = Image.new('RGB', (WIDTH, margin_top * 2 + 2), BACKGROUND_COLOR)
        d = ImageDraw.Draw(img)
        d.text((margin_left + line_width + (WIDTH - 2 * margin_left - 2 * line_width - width) / 2, margin_top - 10),
               text, fill=text_color, font=font)
        d.line((margin_left, margin_top, margin_left + line_width, margin_top), fill=text_color, width=2)
        d.line((WIDTH - margin_left - line_width, margin_top, WIDTH - margin_left, margin_top), fill=text_color,
               width=2)
        return img

    def _get_footer(self):
        fontsize = 12
        margin_left = 70
        margin_top = 40
        line_width_1 = 312
        line_width_2 = 77
        text_color = "#333333"
        text = "© Петрович"
        font = ImageFont.truetype(os.path.join(STATIC_DIR, 'fonts/Alegreya-Regular.ttf'), fontsize, encoding="unic")
        width, height = get_image_size_by_text(text, font)
        img = Image.new('RGB', (WIDTH, margin_top * 2 + 2), BACKGROUND_COLOR)
        d = ImageDraw.Draw(img)
        d.text((margin_left + line_width_1 + (WIDTH - 2 * margin_left - (line_width_1 + line_width_2) - width) / 2,
                margin_top - 10), text, fill=text_color, font=font)
        d.line((margin_left, margin_top, margin_left + line_width_1, margin_top), fill=text_color, width=2)
        d.line((WIDTH - margin_left - line_width_2, margin_top, WIDTH - margin_left, margin_top), fill=text_color,
               width=2)
        return img

    def _get_body(self, msgs):
        images = [self._get_body_item(msg['username'], msg['text'], msg['avatar']) for msg in msgs]
        return self._image_concatenation(images)

    def _get_body_item(self, username, msg, avatar=None):
        margin_top = 10
        margin_bottom = 15
        margin_left = 110
        text_margin_left = 30
        text_margin_top = 10
        avatar_size = (80, 80)
        max_text_width = 290
        text_color = "#000000"
        name_font_size = 21
        message_font_size = 16

        username_start_pos = (margin_left + avatar_size[0] + text_margin_left, margin_top)
        font_username = ImageFont.truetype(os.path.join(STATIC_DIR, 'fonts/Roboto-Regular.ttf'), name_font_size,
                                           encoding="unic")
        font_message = ImageFont.truetype(os.path.join(STATIC_DIR, 'fonts/Roboto-Regular.ttf'), message_font_size,
                                          encoding="unic")

        _, username_height = get_image_size_by_text(username, font_username)
        msg_start_pos = (username_start_pos[0], username_start_pos[1] + username_height + text_margin_top)

        msg_lines = textwrap.wrap(msg, width=int(max_text_width / 7.5))
        total_message_height = sum([font_message.getsize(msg_line)[1] for msg_line in msg_lines])
        total_text_real_height = username_height + text_margin_top + total_message_height
        total_text_height = max(total_text_real_height, avatar_size[0])
        total_height = total_text_height + margin_top + margin_bottom

        img = Image.new('RGB', (WIDTH, total_height), BACKGROUND_COLOR)
        avatar_image = Image.open(avatar)
        avatar_image = self.get_centered_rounded_image(avatar_image)

        avatar_start_pos = (margin_left, (total_text_height - avatar_size[0]) // 2 + margin_top)

        img.paste(avatar_image, avatar_start_pos)

        d = ImageDraw.Draw(img)
        d.text((username_start_pos[0], username_start_pos[1] + (total_text_height - total_text_real_height) // 2),
               username, fill=text_color, font=font_username)
        # d.line((msg_start_pos, msg_start_pos[0] + max_text_width, msg_start_pos[1]), fill=text_color, width=2)
        offset_y = 0
        for line in msg_lines:
            d.text((msg_start_pos[0], msg_start_pos[1] + offset_y + (total_text_height - total_text_real_height) // 2),
                   line, fill=text_color, font=font_message)
            offset_y += font_message.getsize(line)[1]
        return img

    def build_quote_image(self, msgs):
        image_header = self._get_header()
        image_body = self._get_body(msgs)
        image_footer = self._get_footer()
        return self._image_concatenation([image_header, image_body, image_footer])
