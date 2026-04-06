import os
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, ImageDraw
from PIL import ImageFont

from apps.bot.core.messages.attachments.document import DocumentAttachment
from apps.bot.core.messages.attachments.photo import PhotoAttachment
from apps.shared.exceptions import PWarning
from apps.shared.utils.utils import get_image_size_by_text
from petrovich.settings import STATIC_ROOT


class DemotivatorBuilder:
    FONT_NAME = "timesnewroman.ttf"
    BACKGROUND_COLOR = "black"
    FRAME_COLOR = "white"
    TEXT_COLOR = "white"
    MAX_IMAGE_SIDE = 1600
    TITLE_MAX_FONT_HEIGHT_RATIO = 0.16
    SUBTITLE_MAX_FONT_HEIGHT_RATIO = 0.08
    JPEG_QUALITY = 95
    JPEG_SUBSAMPLING = 0

    OUTER_MARGIN_RATIO = 0.12
    FRAME_RATIO = 0.00125
    INNER_IMAGE_PADDING_RATIO = 0.012
    IMAGE_BOTTOM_MARGIN_RATIO = 0.03
    TITLE_FONT_RATIO = 0.125
    SUBTITLE_FONT_RATIO = 0.065
    TITLE_LINE_SPACING_RATIO = 0.28
    SUBTITLE_LINE_SPACING_RATIO = 0.25
    TITLE_SUBTITLE_SPACING_RATIO = 0.15
    BOTTOM_MARGIN_RATIO = 0.065

    def __init__(self, image_attachment: PhotoAttachment | DocumentAttachment, title: str, subtitle: str = ""):
        self.image_attachment = image_attachment
        self.title = title.strip()
        self.subtitle = subtitle.strip()

    def build_bytes(self) -> bytes:
        image = self._open_image()

        min_image_side = min(image.width, image.height)
        outer_margin = max(48, int(min_image_side * self.OUTER_MARGIN_RATIO))
        frame_width = max(1, int(min_image_side * self.FRAME_RATIO))
        inner_image_padding = max(6, int(min_image_side * self.INNER_IMAGE_PADDING_RATIO))
        image_bottom_margin = max(12, int(image.height * self.IMAGE_BOTTOM_MARGIN_RATIO))
        title_font_size = min(
            max(40, int(image.width * self.TITLE_FONT_RATIO)),
            max(40, int(min_image_side * self.TITLE_MAX_FONT_HEIGHT_RATIO)),
        )
        subtitle_font_size = min(
            max(25, int(image.width * self.SUBTITLE_FONT_RATIO)),
            max(25, int(min_image_side * self.SUBTITLE_MAX_FONT_HEIGHT_RATIO)),
        )

        title_font = self._get_font(self.FONT_NAME, title_font_size)
        subtitle_font = self._get_font(self.FONT_NAME, subtitle_font_size)

        text_max_width = image.width
        title_lines = self._wrap_text(self.title, title_font, text_max_width)
        subtitle_lines = self._wrap_text(self.subtitle, subtitle_font, text_max_width) if self.subtitle else []

        title_height = self._get_multiline_height(title_lines, title_font, self.TITLE_LINE_SPACING_RATIO)
        subtitle_height = self._get_multiline_height(subtitle_lines, subtitle_font, self.SUBTITLE_LINE_SPACING_RATIO)
        title_subtitle_spacing = (
            max(8, int((title_font.size + subtitle_font.size) * self.TITLE_SUBTITLE_SPACING_RATIO))
            if subtitle_lines
            else 0
        )
        bottom_margin = max(14, int(image.height * self.BOTTOM_MARGIN_RATIO))

        framed_image_width = image.width + (frame_width + inner_image_padding) * 2
        framed_image_height = image.height + (frame_width + inner_image_padding) * 2
        canvas_width = framed_image_width + outer_margin * 2
        canvas_height = (
            outer_margin
            + framed_image_height
            + image_bottom_margin
            + title_height
            + title_subtitle_spacing
            + subtitle_height
            + bottom_margin
        )

        canvas = Image.new("RGB", (canvas_width, canvas_height), self.BACKGROUND_COLOR)
        draw = ImageDraw.Draw(canvas)

        frame_x = outer_margin
        frame_y = outer_margin
        draw.rectangle(
            (frame_x, frame_y, frame_x + framed_image_width - 1, frame_y + framed_image_height - 1),
            fill=self.FRAME_COLOR,
        )
        draw.rectangle(
            (
                frame_x + frame_width,
                frame_y + frame_width,
                frame_x + framed_image_width - frame_width - 1,
                frame_y + framed_image_height - frame_width - 1,
            ),
            fill=self.BACKGROUND_COLOR,
        )
        canvas.paste(image, (frame_x + frame_width + inner_image_padding, frame_y + frame_width + inner_image_padding))

        current_y = frame_y + framed_image_height + image_bottom_margin
        current_y = self._draw_centered_lines(
            draw,
            title_lines,
            title_font,
            current_y,
            canvas_width,
            self.TITLE_LINE_SPACING_RATIO,
        )

        if subtitle_lines:
            current_y += title_subtitle_spacing
            self._draw_centered_lines(
                draw,
                subtitle_lines,
                subtitle_font,
                current_y,
                canvas_width,
                self.SUBTITLE_LINE_SPACING_RATIO,
            )

        return self._convert_to_jpeg_bytes(canvas)

    def _open_image(self) -> Image.Image:
        try:
            content = self.image_attachment.download_content()
            image = Image.open(BytesIO(content))
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")
            return self._normalize_image_size(image)
        except Exception as exc:
            raise PWarning("Не удалось прочитать изображение для демотиватора") from exc

    def _normalize_image_size(self, image: Image.Image) -> Image.Image:
        if max(image.width, image.height) <= self.MAX_IMAGE_SIDE:
            return image

        resampling = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
        image = image.copy()
        image.thumbnail((self.MAX_IMAGE_SIDE, self.MAX_IMAGE_SIDE), resampling)
        return image

    def _get_font(self, font_name: str, size: int):
        font_path = Path(STATIC_ROOT) / "fonts" / font_name
        if font_path.exists():
            return ImageFont.truetype(os.fspath(font_path), size, encoding="unic")
        raise PWarning(f"Не найден шрифт {font_name} для демотиватора")

    @staticmethod
    def _wrap_text(text: str, font, max_width: int) -> list[str]:
        if not text:
            return []

        wrapped_lines = []
        for line in text.splitlines() or [text]:
            line = line.strip()
            if not line:
                continue

            current_line = ""
            for word in line.split():
                candidate = f"{current_line} {word}".strip()
                if get_image_size_by_text(candidate, font)[0] <= max_width:
                    current_line = candidate
                    continue

                if current_line:
                    wrapped_lines.append(current_line)
                    current_line = ""

                if get_image_size_by_text(word, font)[0] <= max_width:
                    current_line = word
                    continue

                wrapped_lines.extend(DemotivatorBuilder._split_long_word(word, font, max_width))

            if current_line:
                wrapped_lines.append(current_line)
        return wrapped_lines

    @staticmethod
    def _split_long_word(word: str, font, max_width: int) -> list[str]:
        parts = []
        current = ""
        for symbol in word:
            candidate = current + symbol
            if current and get_image_size_by_text(candidate, font)[0] > max_width:
                parts.append(current)
                current = symbol
            else:
                current = candidate
        if current:
            parts.append(current)
        return parts

    def _get_multiline_height(self, lines: list[str], font, spacing_ratio: float) -> int:
        if not lines:
            return 0

        line_heights = [get_image_size_by_text(line, font)[1] for line in lines]
        line_spacing = max(4, int(font.size * spacing_ratio))
        return sum(line_heights) + line_spacing * (len(lines) - 1)

    def _draw_centered_lines(
        self, draw, lines: list[str], font, y: int, canvas_width: int, spacing_ratio: float
    ) -> int:
        line_spacing = max(4, int(font.size * spacing_ratio))
        for index, line in enumerate(lines):
            left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
            line_width = right - left
            line_height = bottom - top
            x = (canvas_width - line_width) // 2 - left
            draw.text((x, y - top), line, fill=self.TEXT_COLOR, font=font)
            y += line_height
            if index != len(lines) - 1:
                y += line_spacing
        return y

    def _convert_to_jpeg_bytes(self, image: Image.Image) -> bytes:
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format="JPEG", quality=self.JPEG_QUALITY, subsampling=self.JPEG_SUBSAMPLING)
        img_byte_arr.seek(0)
        return img_byte_arr.read()
