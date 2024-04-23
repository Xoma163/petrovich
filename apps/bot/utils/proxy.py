from petrovich.settings import env


def get_proxies():
    return {"https": env.str("SOCKS5_PROXY"), "http": env.str("SOCKS5_PROXY")}
