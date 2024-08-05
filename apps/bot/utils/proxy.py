from petrovich.settings import env


def get_proxies():
    return {"https": env.str("PROXY_SOCKS5"), "http": env.str("PROXY_SOCKS5")}
