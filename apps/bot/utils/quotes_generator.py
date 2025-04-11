import textwrap
from io import BytesIO

from PIL import Image, ImageDraw, ImageFilter

from apps.bot.utils.utils import get_image_size_by_text, get_font_by_path


class QuotesGenerator:
    WIDTH = 620
    BACKGROUND_COLOR = "#F5F5F5"

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
        back_color = Image.new(cropped_image.mode, cropped_image.size, self.BACKGROUND_COLOR)
        offset = blur_radius * 2 + offset
        mask = Image.new("RGBA", cropped_image.size, 255)

        draw = ImageDraw.Draw(mask)
        draw.ellipse((offset, offset, cropped_image.size[0] - offset, cropped_image.size[1] - offset),
                     fill=(255, 255, 255))
        mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))
        img_round = Image.composite(cropped_image, back_color, mask)

        img_round.thumbnail((max_size, max_size), Image.LANCZOS)
        return img_round

    @staticmethod
    def get_message_photo(image: Image, max_size=290):
        w, h = image.size
        if w < max_size:
            return image
        k = w / max_size
        new_size = (max_size, h // k)
        image.thumbnail(new_size, Image.LANCZOS)
        return image

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

    def _get_header(self, title):
        fontsize = 12
        margin_left = 70
        margin_top = 40
        line_width = 200
        text_color = "#333333"
        text = title
        font = get_font_by_path("Alegreya-Regular.ttf", fontsize)

        width, _ = get_image_size_by_text(text, font)
        img = Image.new('RGB', (self.WIDTH, margin_top * 2 + 2), self.BACKGROUND_COLOR)
        d = ImageDraw.Draw(img)
        d.text(
            (margin_left + line_width + (self.WIDTH - 2 * margin_left - 2 * line_width - width) / 2, margin_top - 10),
            text, fill=text_color, font=font)
        d.line((margin_left, margin_top, margin_left + line_width, margin_top), fill=text_color, width=2)
        d.line((self.WIDTH - margin_left - line_width, margin_top, self.WIDTH - margin_left, margin_top),
               fill=text_color,
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
        font = get_font_by_path("Alegreya-Regular.ttf", fontsize)

        width, _ = get_image_size_by_text(text, font)
        img = Image.new('RGB', (self.WIDTH, margin_top * 2 + 2), self.BACKGROUND_COLOR)
        d = ImageDraw.Draw(img)
        d.text((margin_left + line_width_1 + (self.WIDTH - 2 * margin_left - (line_width_1 + line_width_2) - width) / 2,
                margin_top - 10), text, fill=text_color, font=font)
        d.line((margin_left, margin_top, margin_left + line_width_1, margin_top), fill=text_color, width=2)
        d.line((self.WIDTH - margin_left - line_width_2, margin_top, self.WIDTH - margin_left, margin_top),
               fill=text_color,
               width=2)
        return img

    def _get_body(self, msgs, this_body_is_fwd=False):
        images = [self._get_body_item(msg['username'], msg['message'], msg['avatar'], msg.get('fwd'), this_body_is_fwd)
                  for msg in msgs]
        return self._image_concatenation(images)

    def _get_body_item(self, username, msg, avatar=None, fwd=None, this_item_is_fwd=False):
        margin_top = 10
        margin_bottom = 15
        margin_left = 110
        text_margin_left = 30
        text_margin_top = 10
        text_body_margin = 3
        avatar_size = (80, 80)
        max_text_width = 290
        text_color = "#000000"
        name_font_size = 21
        message_font_size = 16

        if this_item_is_fwd:
            margin_left = 0
            max_text_width = 215

        username_start_pos = (margin_left + avatar_size[0] + text_margin_left, margin_top)
        font_username = get_font_by_path("Roboto-Regular.ttf", name_font_size)
        font_message = get_font_by_path("Roboto-Regular.ttf", message_font_size)

        _, username_height = get_image_size_by_text(username, font_username)
        msg_start_pos = (username_start_pos[0], username_start_pos[1] + username_height + text_margin_top)

        fwd_photo = None
        fwd_height = 0
        fwd_margin = 0

        msg_photo = None
        msg_photo_height = 0
        msg_photo_margin = 0

        if fwd:
            fwd_photo = self._get_body(fwd, True)
            fwd_height = fwd_photo.height
            fwd_margin = 20
        if msg.get('photo'):
            try:
                image = Image.open(BytesIO(msg['photo']))
            except Exception:
                image = None
            if image:
                composite = Image.new("RGBA", image.size, (255, 255, 255, 0))
                composite.paste(image)

                msg_photo = self.get_message_photo(composite, max_text_width)
                msg_photo_height = msg_photo.height
                msg_photo_margin = 20

        # stack messages from one user aka dancing with ▲
        _msg_lines = [textwrap.wrap(x, width=int(max_text_width / 7.5)) for x in msg['text'].split("▲")]
        msg_lines = []
        while len(_msg_lines) > 0 and not _msg_lines[-1]:
            del _msg_lines[-1]
        for line in _msg_lines:
            if len(line) > 0:
                msg_lines += line
            else:
                msg_lines += [" "]
        total_msg_lines_height = sum([get_image_size_by_text(msg_line, font_message)[1] for msg_line in msg_lines])
        if not total_msg_lines_height:
            msg_photo_margin = 0
            if not msg_photo:
                fwd_margin = 0
        total_msg_lines_height += text_body_margin * len(msg_lines)
        total_height = username_height + text_margin_top + total_msg_lines_height + msg_photo_height + fwd_height
        total_height = max(total_height, avatar_size[1]) + margin_top + margin_bottom + msg_photo_margin + fwd_margin

        img = Image.new('RGB', (self.WIDTH, total_height), self.BACKGROUND_COLOR)
        if avatar:
            try:
                avatar_image = Image.open(avatar)
                avatar_image = self.get_centered_rounded_image(avatar_image)
                avatar_start_pos = (margin_left, margin_top)
                img.paste(avatar_image, avatar_start_pos)
            except Exception as e:
                pass

        d = ImageDraw.Draw(img)
        d.text((username_start_pos[0], username_start_pos[1]), username, fill=text_color, font=font_username)
        # d.line((msg_start_pos, msg_start_pos[0] + max_text_width, msg_start_pos[1]), fill=text_color, width=2)
        offset_y = 0
        for line in msg_lines:
            d.text((msg_start_pos[0], msg_start_pos[1] + offset_y), line, fill=text_color, font=font_message)
            offset_y += get_image_size_by_text(line, font_message)[1] + text_body_margin

        msg_photo_pos = None
        if msg_photo:
            msg_photo_pos = (msg_start_pos[0], msg_start_pos[1] + offset_y + msg_photo_margin)
            # Третий параметр: https://stackoverflow.com/questions/5324647/how-to-merge-a-transparent-png-image-with-another-image-using-pil
            try:
                img.paste(msg_photo, msg_photo_pos, msg_photo)
            except Exception:
                img.paste(msg_photo, msg_photo_pos)
        if fwd_photo:
            if msg_photo_pos:
                msg_fwd_pos = (msg_photo_pos[0], msg_photo_pos[1] + msg_photo.height + fwd_margin)
            else:
                msg_fwd_pos = (msg_start_pos[0], msg_start_pos[1] + offset_y + msg_photo_margin)

            img.paste(fwd_photo, msg_fwd_pos)
        return img

    def build(self, msgs, title):
        image_header = self._get_header(title)
        image_body = self._get_body(msgs)
        image_footer = self._get_footer()
        return self._image_concatenation([image_header, image_body, image_footer])
