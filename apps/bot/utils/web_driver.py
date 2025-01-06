from selenium import webdriver


def get_web_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-crash-reporter")
    return webdriver.Chrome(options=options)
