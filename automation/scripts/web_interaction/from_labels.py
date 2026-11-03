import re
from datetime import date
from functools import wraps
from typing import Callable, Concatenate, ParamSpec

from playwright.sync_api import Locator, Page


def get_for_attr(page: Page, label_re: re.Pattern[str] | str) -> str:
    label_locator = page.locator("label", has_text=label_re)
    label_locator.wait_for(state="attached", timeout=5000)

    for_attr = label_locator.first.get_attribute("for")
    if not for_attr:
        raise RuntimeError(f"Cannot find box for {label_re}")
    return for_attr


P = ParamSpec("P")


def for_attr(tag: Callable[[str], str]):
    def deco(
        fn: Callable[Concatenate[Locator, P], None],
    ) -> Callable[Concatenate[Page, re.Pattern[str] | str, P], None]:
        @wraps(fn)
        def wrapper(
            page: Page,
            label_re: re.Pattern[str] | str,
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> None:
            for_attr = get_for_attr(page, label_re)
            box = page.locator(tag(for_attr)).first
            box.wait_for(state="visible", timeout=5000)
            fn(box, *args, **kwargs)

        return wrapper

    return deco


@for_attr(lambda for_attr: f"input#{for_attr}")
def fill_start_date(box: Locator, start_date: date):
    box.fill(f"{start_date.day:02d}/{start_date.month:02d}/{start_date.year}")


@for_attr(lambda for_attr: f"input#{for_attr} + input")
def fill_start_time(box: Locator, start_time: str):
    box.fill(start_time)


@for_attr(lambda for_attr: f"input#{for_attr.replace('txtFromDate', 'txtToDate')}")
def fill_end_date(box: Locator, end_date: date):
    box.fill(f"{end_date.day:02d}/{end_date.month:02d}/{end_date.year}")


@for_attr(
    lambda for_attr: f"input#{for_attr.replace('txtFromDate', 'txtToDate')} + input"
)
def fill_end_time(box: Locator, end_time: str):
    box.fill(end_time)


def fill_start_info(
    page: Page, start_date: date, start_time: str, label_re: re.Pattern[str] | str
):
    fill_start_date(page, label_re, start_date)
    fill_start_time(page, label_re, start_time)


def fill_start_end_time(
    page: Page,
    start_date: date,
    start_time: str,
    end_date: date,
    end_time: str,
    label_re: re.Pattern[str] | str,
):
    fill_start_date(page, label_re, start_date)
    fill_start_time(page, label_re, start_time)
    fill_end_date(page, label_re, end_date)
    fill_end_time(page, label_re, end_time)


def radio_select(page: Page, item_number: int, label_re: re.Pattern[str] | str):
    for_attr = get_for_attr(page, label_re)

    tr = page.locator(f"table#{for_attr} tbody tr")
    if tr.count() < item_number:
        raise RuntimeError(f"need >= {item_number} items, but found {tr.count()}")
    radio = tr.nth(item_number - 1).locator("td input")
    radio.wait_for(state="visible", timeout=5000)
    radio.check()


def fill_textbox(page: Page, text: str, label_re: re.Pattern[str] | str):
    for_attr = get_for_attr(page, label_re)

    input_box = page.locator(f"input#{for_attr}")

    input_box.wait_for(state="visible", timeout=5000)

    input_box.fill(text)


def dropdown_select(page: Page, option_text: str, label_re: re.Pattern[str] | str):
    for_attr = get_for_attr(page, label_re)

    select_list = page.locator(f"select#{for_attr}")

    select_list.wait_for(state="visible", timeout=5000)

    select_list.select_option(option_text)


def tick_checkbox(page: Page, label_re: re.Pattern[str] | str):
    for_attr = get_for_attr(page, label_re)

    checkbox = page.locator(f"input#{for_attr}")

    checkbox.wait_for(state="visible", timeout=5000)

    checkbox.check()
