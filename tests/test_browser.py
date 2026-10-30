import os

import pytest


@pytest.mark.browser
@pytest.mark.skipif(os.getenv("RUN_BROWSER_TESTS") != "1", reason="set RUN_BROWSER_TESTS=1 with a local app running")
def test_dashboard_and_navigation_with_keyboard_and_browser():
    from playwright.sync_api import sync_playwright

    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.set_extra_http_headers({"X-Dev-User": "browser@example.test"})
        page.goto(base_url + "/dashboard")
        assert page.get_by_role("heading", name="Welcome").is_visible()
        assert page.get_by_role("navigation", name="Main navigation").get_by_role("link", name="Lab workspace").is_visible()
        page.keyboard.press("Tab")
        assert page.locator(":focus").count() == 1
        page.get_by_role("link", name="Practice").click()
        assert page.get_by_role("heading", name="Practice questions").is_visible()
        browser.close()
