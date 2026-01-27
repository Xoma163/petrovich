import re


def replace_markdown_links(text: str, bot) -> str:
    p = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    for item in reversed(list(p.finditer(text))):
        start_pos, end_pos = item.span()
        link_text = item.group(1)
        link = item.group(2)
        tg_url = bot.get_formatted_url(link_text, link)
        text = text[:start_pos] + tg_url + text[end_pos:]
    return text


def markdown_wrap_symbols(text):
    return text \
        .replace(">", "&gt;") \
        .replace("<", "&lt;") \
        .replace("&lt;pre&gt;", "<pre>") \
        .replace("&lt;/pre&gt;", "</pre>")


def markdown_to_html(text: str, bot) -> str:
    """
    Переводит из Markdown в html теги.
    Возвращает новую строку и флаг были ли сделаны изменения
    """
    # text_copy = text
    text = markdown_wrap_symbols(text)
    if bot.PRE_TAG:
        if bot.CODE_TAG:
            text = replace_pre_tag(text, bot, '```', '```')
        else:
            text = replace_tag(text, '```', '```', f"<{bot.PRE_TAG}>", f"</{bot.PRE_TAG}>")

    if bot.CODE_TAG:
        text = replace_tag(text, '`', '`', f"<{bot.CODE_TAG}>", f"</{bot.CODE_TAG}>")
    if bot.BOLD_TAG:
        text = replace_tag(text, '**', '**', f"<{bot.BOLD_TAG}>", f"</{bot.BOLD_TAG}>")
    if bot.ITALIC_TAG:
        text = replace_tag(text, '*', '*', f"<{bot.ITALIC_TAG}>", f"</{bot.ITALIC_TAG}>")
    if bot.QUOTE_TAG:
        text = replace_tag(text, '\n&gt;', '\n', f"\n<{bot.QUOTE_TAG}>", f"</{bot.QUOTE_TAG}>\n")
    elif bot.CODE_TAG:
        text = replace_tag(text, '\n&gt;', '\n', f"\n<{bot.CODE_TAG}>", f"</{bot.CODE_TAG}>\n")
    if bot.LINK_TAG:
        text = replace_markdown_links(text, bot)
    return text  # , text_copy != text


def replace_tag(text: str, start_tag: str, end_tag: str, new_start_tag: str, new_end_tag: str):
    start_tag_len = len(start_tag)
    end_tag_len = len(end_tag)

    start_tag_pos = 0
    while True:
        start_tag_pos = text.find(start_tag, start_tag_pos)
        end_tag_pos = text.find(end_tag, start_tag_pos + 1)

        if start_tag_pos == -1 or end_tag_pos == -1:
            break

        # Не трогаем то, что внутри <code>
        # костыльненько
        to_replace_and_next = text[start_tag_pos:]
        close_code_block_pos = to_replace_and_next.find("</code>")
        open_code_block_pos = to_replace_and_next.find("<code")

        escape_tag = False
        if close_code_block_pos != -1:
            if open_code_block_pos != -1:
                if close_code_block_pos < open_code_block_pos:
                    escape_tag = True
            else:
                escape_tag = True

        if escape_tag:
            start_tag_pos += len(start_tag)
            continue

        # strip - экспериментально
        inner_text = text[start_tag_pos + start_tag_len:end_tag_pos].strip()
        new_inner = new_start_tag + inner_text + new_end_tag
        inner_to_replace = text[start_tag_pos:end_tag_pos + end_tag_len]
        text = text.replace(inner_to_replace, new_inner)

        start_tag_pos = start_tag_pos + len(new_inner)
    return text


def replace_pre_tag(text: str, bot, start_tag: str, end_tag: str):
    start_tag_len = len(start_tag)
    end_tag_len = len(end_tag)

    start_tag_pos = 0
    while True:
        start_tag_pos = text.find(start_tag, start_tag_pos)
        end_tag_pos = text.find(end_tag, start_tag_pos + 1)

        if start_tag_pos == -1 or end_tag_pos == -1:
            break

        start_language_pos = start_tag_pos + start_tag_len
        end_language_pos = text.find('\n', start_tag_pos)
        language = text[start_language_pos:end_language_pos]
        if '`' in language or ' ' in language:
            language = ""

        inner_to_replace = text[start_tag_pos:end_tag_pos + end_tag_len]
        # strip - плохо режет слева, rstrip - экспериментально
        inner_text = text[start_tag_pos + start_tag_len + 1 + len(language):end_tag_pos].rstrip()
        new_inner = bot.get_formatted_text(inner_text, language)
        text = text.replace(inner_to_replace, new_inner)

        start_tag_pos = start_tag_pos + len(new_inner)
    return text
