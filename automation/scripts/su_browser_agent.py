#!/usr/bin/python

import os
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

from data_model import ElectionDataWithStrings
from data_parser import parse_data_from_paths
from election_abbr import ELECTION_ABBREVIATION, ELECTION_FILE_EXTENSION
from playwright.sync_api import Page, sync_playwright
from web_interaction.from_labels import (
    dropdown_select,
    fill_start_end_time,
    fill_start_info,
    fill_textbox,
    get_for_attr,
    radio_select,
)
from web_interaction.navigation import (
    click_button,
    click_first_button_expect_navigation,
    fill_box,
    fill_first_box,
    goto_url_and_wait_for_it,
)

# ROOT = Path(__file__).resolve().parents[1]
# sys.path.insert(0, str(ROOT))

day_of_week_offset_map = {
    "Sunday": -1,
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
}

ORGANISATION_ID = "6408"

MODE: Literal["CREATE", "POSITIONS", "CANDIDATES"] = "CANDIDATES"

positions_to_skip = []

PROFILE_DIR = Path.home() / ".local" / "share" / "playwright-firefox-bot-profile"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

RO_DIRECTORY = Path(os.getcwd())

DATA_FILE = (
    RO_DIRECTORY
    / "elections"
    / f"election-{ELECTION_ABBREVIATION}.{ELECTION_FILE_EXTENSION}"
)
POSITIONS_FILE = RO_DIRECTORY / "positions" / "positions.json"
RESTRICTIONS_FILE = RO_DIRECTORY / "sjc-restrictions.json"
DESCRIPTIONS_DIR = RO_DIRECTORY / "positions" / "descriptions"
CANDIDATE_FILE = RO_DIRECTORY / "elections" / f"candidates-{ELECTION_ABBREVIATION}.json"
if not os.path.exists(CANDIDATE_FILE):
    CANDIDATE_FILE = None  # pyright: ignore[reportConstantRedefinition]
CANDIDATE_FOLDER = RO_DIRECTORY / "elections" / f"{ELECTION_ABBREVIATION}-candidates"
if not os.path.exists(CANDIDATE_FOLDER):
    CANDIDATE_FOLDER = None  # pyright: ignore[reportConstantRedefinition]

# Date format: YYYY, M, D
MONDAY_FIRST_WEEK = date(2026, 4, 27)


class ElectionDataMissingException(Exception):
    pass


class ElectionDataParsingException(Exception):
    pass


def main():
    election_data = parse_data_from_paths(
        DATA_FILE,
        POSITIONS_FILE,
        RESTRICTIONS_FILE,
        DESCRIPTIONS_DIR,
        CANDIDATE_FILE,
        ELECTION_ABBREVIATION,
    )

    with sync_playwright() as p:

        context = p.firefox.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), headless=False
        )

        page = context.new_page()

        page.goto("https://www.oxfordsu.org/admin/elections/" + ORGANISATION_ID)

        if MODE == "CANDIDATES":
            candidates_fill(page, election_data)

        elif MODE == "CREATE":
            new_election_fill(page, election_data)

        elif MODE == "POSITIONS":
            positions_fill(page, election_data)
        else:
            pass

        context.close()


def candidates_fill(page: Page, election_data: ElectionDataWithStrings):
    election_number = input("Log in. Enter the election number: ")
    if not election_data.positions_with_candidates:
        raise ElectionDataMissingException(
            "No positions with candidates (so no candidates)"
        )

    for pos, cans in election_data.positions_with_candidates:
        if pos.id in positions_to_skip:
            print(f"Skipping {pos.id}")
            time.sleep(1)
            continue

        goto_url_and_wait_for_it(
            page, "https://www.oxfordsu.org/admin/elections/posts/" + election_number
        )

        click_first_button_expect_navigation(
            page, f"div.reorder-list a[title*='{pos.su_platform_name}']"
        )

        # https://www.oxfordsu.org/admin/elections/post/2169/10157/
        current_page = page.url

        # https://www.oxfordsu.org/admin/elections/candidatelist/2169/10157/
        candidate_page = re.sub(
            r"^(.*)elections/post(.*)$",
            r"\1elections/candidatelist\2",
            current_page,
        )

        time.sleep(1)

        goto_url_and_wait_for_it(page, candidate_page)

        for candidate in cans:
            # Fill candidate box with candidate name
            fill_box(page, "div.input-group input.form-control", candidate.full_name)

            # Click the Find Person button: value "Find Person"
            click_button(
                page,
                "input[type='submit'][value='Find Person']",
            )

            # Get the user to select the person (or give the names and have them choose)

            print(
                f'Select the "Select" button next to the correct person {candidate.full_name}'
            )
            print("I will wait for the redirect")

            # Wait for redirect to https://www.oxfordsu.org/admin/elections/candidate/2169/137529/10157/

            target_regex = re.compile(
                r"https://www.oxfordsu.org/admin/elections/candidate/.*"
            )

            try:
                page.wait_for_url(target_regex, timeout=1000 * 1000)
                print("redirected")

            except Exception:
                print("Timed-out")
                sys.exit(1)
            # Input the Display Name (candidate.manifesto_name) into input with title "Display name"

            fill_textbox(page, candidate.manifesto_name, "Display name")

            # Check the email is what we except - div.vp_content link with href mailto: ...
            # candidate.email

            for_attr = get_for_attr(page, "Email")
            email_box = page.locator(f"a#{for_attr}")
            email_box.wait_for(state="visible", timeout=5000)
            if email_box.inner_text().lower() != candidate.email.lower():
                print(f"Emails don't match {email_box.inner_text()}, {candidate.email}")

            # Click Create Profile (input.button, type="submit", value: Create Profile)

            try:
                create_profile_button = page.locator(
                    "input[type='submit'][value='Create profile']"
                )
                create_profile_button.wait_for(state="visible", timeout=5000)
            except Exception:
                create_profile_button = page.locator(
                    "input[type='submit'][value='Update profile']"
                )
                create_profile_button.wait_for(state="visible", timeout=5000)

            create_profile_button.click()

            time.sleep(5)

            # Click Submit Nomination (input.button, type="submit", value: Submit Nomination)
            try:
                submit_nomination_button = page.locator(
                    "input[type='submit'][value='Submit nomination']"
                )

                submit_nomination_button.wait_for(state="visible", timeout=5000)
            except Exception:
                submit_nomination_button = page.locator(
                    "input[type='submit'][value='Update nomination']"
                )

                submit_nomination_button.wait_for(state="visible", timeout=5000)

            submit_nomination_button.click()

            time.sleep(5)

            candidate_creation_page = page.url

            # Go back to candidates page
            page.goto(candidate_page)
            page.wait_for_url(candidate_page)

            # Select the name of the person just created

            url_end = candidate_creation_page.removeprefix("https://oxfordsu.org")

            table = page.locator(  # pyright: ignore[reportUnusedVariable]
                f"table tbody td a[href='{url_end}']"
            )

            # Go edit the manifesto

            time.sleep(60)
            # sys.exit(1)

            # Now on https://www.oxfordsu.org/admin/elections/candidate/editmanifesto/2169/10157/23335/

            input(
                f"Please find the photo {candidate.photo_file_name}, upload it, and use the file {candidate.manifesto_files_path}/{candidate.manifesto_text_file_name} to create the manifesto. Press enter when done. "
            )

            # Find Photo "Browse" button (type="file")

            # Click it, tell the user what file they need to select

            # Wait for file name to appear, click the "Upload" button

            # Wait for refresh

            # Input Manifesto in manifesto box (in the iframe)

            # Get the user to fix formatting and press enter when done

            # Click save (or if the user does this continue??)

            # Wait for reload and "Changes saved" to appear

            # Go back to candidate list

            time.sleep(1)

            page.goto(candidate_page)

            time.sleep(1)

        time.sleep(5)

        # Go to https://www.oxfordsu.org/admin/elections/candidates/2169/

        page.goto(
            "https://www.oxfordsu.org/admin/elections/candidates/" + election_number
        )

        # Find drop down (current status of Unapproved)
        # <select> with options
        # Change to Approved
        # dropdown_select(page, "Approved", "Current status")

        # # Click the Update button
        # click_button(
        #     page,
        #     "div.vpFormSubmit.clearfix input.button[type='submit'][value='Update']",
        # )

        # alerts don't really work in playwright
        # Click the "Approve all candidates" button (just in case)

        # Click yes on the JS alert (or get the user to do this)


def new_election_fill(page: Page, election_data: ElectionDataWithStrings):
    input("Log in. Then Press enter")
    # Just view /admin/elections/election/6408
    # to create a New Election
    page.goto("https://www.oxfordsu.org/admin/elections/election/" + ORGANISATION_ID)

    # Fill title box with election title
    fill_box(
        page,
        "input[title='Title']",
        f"{election_data.term_first_letter}T{election_data.padded_year_mod_100} {election_data.election_type}Election{election_data.space_plus_by_election_number}",
    )

    if election_data.polls_open is None or election_data.polls_open.week is None:
        raise ElectionDataMissingException("Missing polls open or polls open week")

    display_start_day = MONDAY_FIRST_WEEK + timedelta(
        days=-1 + (election_data.polls_open.week - 1) * 7 - 14
    )

    # Display period
    fill_start_end_time(
        page,
        display_start_day,
        "00:00",
        display_start_day + timedelta(days=29),
        "12:00",
        "Display period",
    )

    # Nominations
    fill_start_end_time(
        page,
        display_start_day,
        "00:01",
        display_start_day,
        "00:02",
        "Nominations Period",
    )

    # Online Manifestos
    fill_start_info(page, display_start_day, "00:03", "Online Manifesto Deadline")

    # Paper Manifestos
    fill_start_info(page, display_start_day, "00:03", "Paper Manifesto Deadline")

    # Hide for logged-in non-John's students
    radio_select(page, 4, re.compile(r"Logged in users"))

    polls_open_date = MONDAY_FIRST_WEEK + timedelta(
        days=(
            day_of_week_offset_map.get(election_data.polls_open.day, 0)
            + (election_data.polls_open.week - 1) * 7
        )
    )

    if election_data.polls_close is None or election_data.polls_close.week is None:
        raise ElectionDataMissingException("Missing polls close or polls close week")

    polls_close_date = MONDAY_FIRST_WEEK + timedelta(
        days=(
            day_of_week_offset_map.get(election_data.polls_close.day, 0)
            + (election_data.polls_close.week - 1) * 7
        )
    )

    if election_data.polls_close.time is None or election_data.polls_open.time is None:
        raise ElectionDataMissingException("Missing polls open or close time")

    polls_open_time = election_data.polls_open.time
    polls_close_time = election_data.polls_close.time

    # TODO, better parsing
    if polls_open_time[-2:] == "am":
        polls_open_hours = int(polls_open_time[:-2])
    elif polls_open_time[-2:] == "pm":
        polls_open_hours = int(polls_open_time[:-2]) + 12
    else:
        raise ElectionDataParsingException(
            "Error parsing polls open time (does not end with am or pm)"
        )

    if polls_close_time[-2:] == "am":
        polls_close_hours = int(polls_close_time[:-2])
    elif polls_close_time[-2:] == "pm":
        polls_close_hours = int(polls_close_time[:-2]) + 12
    else:
        raise ElectionDataParsingException(
            "Error parsing polls close time (does not end with am or pm)"
        )

    fill_start_end_time(
        page,
        polls_open_date,
        f"{polls_open_hours:02d}:00",
        polls_close_date,
        f"{polls_close_hours:02d}:00",
        "Polling period",
    )

    # Click the save election button
    click_button(page, 'input[type="submit"][value="Save Election"]')

    time.sleep(15)


def positions_fill(page: Page, election_data: ElectionDataWithStrings):
    election_number = input("Log in. Enter the election number: ")

    if not election_data.positions_with_candidates:
        raise ElectionDataMissingException("Missing candidates")

    for pos_can in election_data.positions_with_candidates:
        pos = pos_can[0]

        # Go to add new post page directly
        goto_url_and_wait_for_it(
            page, "https://www.oxfordsu.org/admin/elections/post/" + election_number
        )

        # Put Officer Name in the box (first textbox)
        fill_first_box(page, "input.form-control", pos.su_platform_name[:-1])

        # Get user to select
        input(
            f"Please enter the last character {pos.su_platform_name[-1]} on the website and select the correct group posting, and then press enter here: "
        )

        # Places
        fill_textbox(page, f"{pos.position_count}", "Places")

        # Manifesto type: Free text (drop down box)
        dropdown_select(page, "Free-text manifesto document", "Manifesto type")

        # Require photo (drop down)
        dropdown_select(page, "Photo is required", "Photo option")

        # Click save button
        click_button(page, "input[type='submit'][value='Save']")

        # We should really check the word "saved" comes up newly on the screen
        time.sleep(1)


if __name__ == "__main__":
    main()
