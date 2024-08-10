from petrovich.settings import env


def get_proxies():
    return _get_proxies("PROXY_SOCKS5")


def get_http_proxies():
    return _get_proxies("PROXY_HTTP")


def get_proxies_sweden():
    return _get_proxies("PROXY_SOCKS5_SWEDEN")


def _get_proxies(env_name: str):
    return {"https": env.str(env_name), "http": env.str(env_name)}
