from selenium import webdriver


def get_web_driver(proxy=None, headers=None):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-crash-reporter")
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
    if headers:
        for header in headers:
            options.add_argument(f"{header}={headers[header]}")
        options.add_argument('user-agent=ТВОЙ_АГЕНТ')
    return webdriver.Chrome(options=options)
