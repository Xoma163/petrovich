import os
from glob import glob

from selenium import webdriver
from selenium.webdriver.chrome.service import Service


def _latest_existing(pattern: str) -> str | None:
    paths = [path for path in glob(pattern) if os.path.exists(path)]
    return sorted(paths)[-1] if paths else None


def _get_chrome_binary() -> str | None:
    return (
        os.environ.get("CHROME_BINARY")
        or _latest_existing("/home/andrewsha/.cache/selenium/chrome/linux64/*/chrome")
        or ("/opt/google/chrome/chrome" if os.path.exists("/opt/google/chrome/chrome") else None)
    )


def _get_chromedriver_binary() -> str | None:
    return (
        os.environ.get("CHROMEDRIVER_BINARY")
        or _latest_existing("/home/andrewsha/.cache/selenium/chromedriver/linux64/*/chromedriver")
        or ("/usr/local/bin/chromedriver" if os.path.exists("/usr/local/bin/chromedriver") else None)
    )


def get_web_driver(headers=None) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()

    chromium_binary = _get_chrome_binary()
    chromedriver_binary = _get_chromedriver_binary()
    if chromium_binary:
        options.binary_location = chromium_binary

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-crash-reporter")
    options.add_argument("--disable-gpu")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
    )

    # if proxy:
    #     options.add_argument(f"--proxy-server={proxy}")
    if headers:
        for header in headers:
            options.add_argument(f"{header}={headers[header]}")

    service = Service(chromedriver_binary) if chromedriver_binary else None
    driver = webdriver.Chrome(service=service, options=options) if service else webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd(
        "Network.setExtraHTTPHeaders",
        {
            "headers": {
                "Accept-Language": "en-US,en;q=0.9",
            },
        },
    )
    driver.execute_cdp_cmd("Emulation.setLocaleOverride", {"locale": "en-US"})
    return driver


# https://stackoverflow.com/a/64630427
def get_web_driver_headers(web_driver: webdriver.Chrome) -> dict[str, str]:
    headers = web_driver.execute_script(
        "var req = new XMLHttpRequest();req.open('GET', document.location, false);req.send(null);return req.getAllResponseHeaders()"
    )
    return dict([x.split(": ", 1) for x in headers.strip().split("\r\n") if x])
