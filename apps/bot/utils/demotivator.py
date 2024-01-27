import os

from PIL import Image, ImageDraw, ImageFont

from apps.bot.utils.utils import get_image_size_by_text
from petrovich.settings import STATIC_ROOT


class DemotivatorText:
    def __init__(self, text, font_size, color, padding, margin, available_width):
        self.text = text
        font_path = os.path.join(STATIC_ROOT, 'fonts/TimesNewRoman.ttf')
        self.font = ImageFont.truetype(font_path, font_size)
        self.color = color
        self.padding = padding
        self.margin = margin

        self.lines = self._get_lines(available_width)
        self.height = self._get_height()

    def __bool__(self):
        return bool(self.text)

    def _get_lines(self, available_width):
        tw = TextWrapper(self.text, self.font, available_width)
        tw.calculate()
        return tw.get_wrapped_lines()

    def _get_height(self):
        total_height = 0
        for line in self.lines:
            total_height += get_image_size_by_text(line, self.font)[1] + self.padding
        return total_height + self.margin


class DemotivatorBuilder:
    def __init__(self, image, text1="", text2=""):
        # LR TB
        self.BLACK_OUTER_FRAME = (68, 36)
        self.WHITE_FRAME = (3, 3)
        self.BLACK_INNER_FRAME = (4, 3)

        self.MAX_IMAGE_WIDTH = 600

        self.image = image
        self.demotivator = None

        self._prepare_image()
        self._calculate_available_text_width()
        self.text1 = DemotivatorText(text1, 60, 'white', 0, 22, self.available_text_width)
        self.text2 = DemotivatorText(text2, 30, 'white', 0, 25, self.available_text_width)
        self._set_demotivator()

    def _prepare_image(self):
        if self.image.width > self.MAX_IMAGE_WIDTH:
            new_image_width = self.MAX_IMAGE_WIDTH
            new_image_height = int(self.image.height / self.image.width * self.MAX_IMAGE_WIDTH)
            self.image = self.image.resize((new_image_width, new_image_height))

    def _calculate_available_text_width(self):
        self.available_text_width = self.image.width + \
                                    self.BLACK_OUTER_FRAME[0] + self.WHITE_FRAME[0] * 2 + self.BLACK_INNER_FRAME[0] * 2

    def _get_demotivator_sizes(self):
        def get_x():
            return 2 * (self.BLACK_OUTER_FRAME[0] + self.WHITE_FRAME[0] + self.BLACK_INNER_FRAME[0]) + self.image.width

        def get_y():
            return 2 * (self.BLACK_OUTER_FRAME[1] + self.WHITE_FRAME[1] + self.BLACK_INNER_FRAME[1]) + \
                self.image.height + self.text1.height + self.text2.height

        return get_x(), get_y()

    def _set_demotivator(self):
        self.demotivator = Image.new("RGB", self._get_demotivator_sizes(), color="black")

        image_offset = (self.BLACK_OUTER_FRAME[0] + self.WHITE_FRAME[0] + self.BLACK_INNER_FRAME[0],
                        self.BLACK_OUTER_FRAME[1] + self.WHITE_FRAME[1] + self.BLACK_INNER_FRAME[1])
        self.demotivator.paste(self.image, image_offset)

    def _draw_lines(self):
        demotivator_draw = ImageDraw.Draw(self.demotivator)
        demotivator_draw.rectangle(
            (self.BLACK_OUTER_FRAME[0],
             self.BLACK_OUTER_FRAME[1],
             self.BLACK_OUTER_FRAME[0] + 2 * (self.WHITE_FRAME[0] + self.BLACK_INNER_FRAME[0]) + self.image.width,
             self.BLACK_OUTER_FRAME[1] + 2 * (self.WHITE_FRAME[1] + self.BLACK_INNER_FRAME[1]) + self.image.height),
            outline='white',
            width=3)
        demotivator_draw.rectangle(
            (self.BLACK_OUTER_FRAME[0] + self.WHITE_FRAME[0],
             self.BLACK_OUTER_FRAME[1] + self.WHITE_FRAME[1],
             self.BLACK_OUTER_FRAME[0] + self.WHITE_FRAME[0] + 2 * self.BLACK_INNER_FRAME[0] + self.image.width,
             self.BLACK_OUTER_FRAME[1] + self.WHITE_FRAME[1] + 2 * self.BLACK_INNER_FRAME[1] + self.image.height),
            outline='black',
            width=3)

    def _draw_texts_lines(self, text_obj, drawing, pos_y):

        max_text_height = max([get_image_size_by_text(line, font=text_obj.font)[1] for line in text_obj.lines])
        for line in text_obj.lines:
            text_width = get_image_size_by_text(line, font=text_obj.font)[0]
            pos_x = int((self.available_text_width - text_width + self.BLACK_OUTER_FRAME[0]) / 2)
            drawing.text((pos_x, pos_y), line, font=text_obj.font)
            pos_y += max_text_height + text_obj.padding
        return pos_y

    def _draw_texts(self):
        demotivator_draw = ImageDraw.Draw(self.demotivator)
        pos_y = int(self.BLACK_OUTER_FRAME[1] + self.WHITE_FRAME[1] + self.BLACK_INNER_FRAME[
            1] + self.image.height + self.text1.margin)
        pos_y = self._draw_texts_lines(self.text1, demotivator_draw, pos_y)
        if self.text2:
            pos_y += self.text2.margin
            self._draw_texts_lines(self.text2, demotivator_draw, pos_y)

    def get_demotivator(self):
        self._draw_lines()
        self._draw_texts()
        return self.demotivator


class TextWrapper(object):
    """ Helper class to wrap text in lines, based on given text, font
        and max allowed line width.
    """

    def __init__(self, text, font, max_width):
        self.text = text
        self.text_lines = [
            ' '.join([w.strip() for w in l.split(' ') if w])
            for l in text.split('\n')
            if l
        ]
        self.font = font
        self.max_width = max_width

        self.draw = ImageDraw.Draw(
            Image.new(
                mode='RGB',
                size=(100, 100)
            )
        )
        self.space_width = get_image_size_by_text(' ', self.font)[0]
        self.wrapped_text = ""
        self.wrapped_lines = []

    def get_text_width(self, text):
        return get_image_size_by_text(text, self.font)[0]

    def calculate(self):
        wrapped_lines = []
        buf = []
        buf_width = 0

        for line in self.text_lines:
            for word in line.split(' '):
                word_width = self.get_text_width(word)

                expected_width = word_width if not buf else \
                    buf_width + self.space_width + word_width

                if expected_width <= self.max_width:
                    # word fits in line
                    buf_width = expected_width
                    buf.append(word)
                else:
                    # word doesn't fit in line
                    wrapped_lines.append(' '.join(buf))
                    buf = [word]
                    buf_width = word_width

            if buf:
                wrapped_lines.append(' '.join(buf))
                buf = []
                buf_width = 0
        self.wrapped_text = '\n'.join(wrapped_lines)
        self.wrapped_lines = wrapped_lines

    def get_wrapped_lines(self):
        return self.wrapped_lines

    def get_wrapped_text(self):
        return self.wrapped_text
