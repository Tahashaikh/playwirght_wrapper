import re
from playwright.sync_api import Page, expect


def test_secret_sauce_one(page: Page) -> None:
    page.goto("https://demo.automationtesting.in/FileUpload.html")
    page.pause()

