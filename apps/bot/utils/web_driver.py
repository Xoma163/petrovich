from selenium import webdriver


def get_web_driver(proxy=None):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-crash-reporter")
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")  # сюда свой хост:порт
    return webdriver.Chrome(options=options)
