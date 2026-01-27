from enum import StrEnum


class TelegramParseMode(StrEnum):
    HTML = "HTML"
    MARKDOWN = "Markdown"  # legacy
    MARKDOWN_V2 = "MarkdownV2"
