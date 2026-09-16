from __future__ import annotations

from functools import wraps
from typing import Callable, Concatenate, ParamSpec

from playwright.sync_api import Locator, Page

P = ParamSpec("P")


def wait_for_locator_with_page(
    fn: Callable[Concatenate[Page, Locator, P], None],
) -> Callable[Concatenate[Page, str, P], None]:
    @wraps(fn)
    def wrapper(page: Page, locator: str, *args: P.args, **kwargs: P.kwargs) -> None:
        element = page.locator(locator)
        element.wait_for(state="visible", timeout=5000)
        fn(page, element, *args, **kwargs)

    return wrapper


def wait_for_locator(require_first: bool = False):
    def deco(
        fn: Callable[Concatenate[Locator, P], None],
    ) -> Callable[Concatenate[Page, str, P], None]:
        @wraps(fn)
        def wrapper(
            page: Page, locator: str, *args: P.args, **kwargs: P.kwargs
        ) -> None:
            element = page.locator(locator)
            if require_first:
                element = element.first
            element.wait_for(state="visible", timeout=5000)
            fn(element, *args, **kwargs)

        return wrapper

    return deco


@wait_for_locator()
def fill_box(element: Locator, fill_string: str):
    element.fill(fill_string)


@wait_for_locator(True)
def fill_first_box(element: Locator, fill_string: str):
    element.fill(fill_string)


@wait_for_locator()
def click_button(element: Locator):
    element.click()


@wait_for_locator()
def click_first_button(element: Locator):
    element.click()


@wait_for_locator_with_page
def click_first_button_expect_navigation(page: Page, element: Locator):
    with page.expect_navigation():
        element.click()


def goto_url_and_wait_for_it(page: Page, url: str):
    page.goto(url)
    # page.wait_for_url(url)
