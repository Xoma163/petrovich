import re

from markdown_it import MarkdownIt


def markdown_wrap_symbols(text):
    return (
        text.replace(">", "&gt;").replace("<", "&lt;").replace("&lt;pre&gt;", "<pre>").replace("&lt;/pre&gt;", "</pre>")
    )

# TODO: unused
def has_markdown(text: str) -> bool:
    patterns = [
        r"(^|\n)#{1,6}\s+\S+",  # заголовки
        r"(\*\*|__)(?=\S).+?(?<=\S)\1",  # bold
        r"(\*|_)(?=\S).+?(?<=\S)\1",  # italic
        r"`[^`]+`",  # inline code
        r"!\[[^\]]*\]\([^)]+\)",  # image
        r"\[[^\]]+\]\([^)]+\)",  # link
        r"(^|\n)> .+",  # quote
        r"(^|\n)([-*+]|[0-9]+\.)\s+",  # list
    ]
    return any(re.search(p, text, re.M) for p in patterns)

# TODO: potentially unused
def markdown_to_html(text: str):
    md = MarkdownIt("commonmark", {"html": True, "breaks": True})
    return md.render(text)
