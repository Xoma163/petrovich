from selenium import webdriver


def get_web_driver(headers=None) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-crash-reporter")
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36')

    # if proxy:
    #     options.add_argument(f"--proxy-server={proxy}")
    if headers:
        for header in headers:
            options.add_argument(f"{header}={headers[header]}")
    return webdriver.Chrome(options=options)


# https://stackoverflow.com/a/64630427
def get_web_driver_headers(web_driver: webdriver.Chrome) -> dict[str, str]:
    headers = web_driver.execute_script(
        "var req = new XMLHttpRequest();"
        "req.open('GET', document.location, false);"
        "req.send(null);"
        "return req.getAllResponseHeaders()"
    )
    return dict(
        [x.split(': ', 1) for x in headers.strip().split('\r\n') if x]
    )
