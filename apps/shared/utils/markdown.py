def markdown_wrap_symbols(text):
    return text \
        .replace(">", "&gt;") \
        .replace("<", "&lt;") \
        .replace("&lt;pre&gt;", "<pre>") \
        .replace("&lt;/pre&gt;", "</pre>")
