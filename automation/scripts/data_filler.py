#!/usr/bin/python

"""
This allows filling out all the templates for the current election for which we have the correct data.
"""

import os
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from data_model import ElectionDataWithStrings
from data_parser import parse_data_from_paths, write_template_if_have_data
from election_abbr import ELECTION_ABBREVIATION
from templates import create_templates

RO_DIRECTORY = Path(os.getcwd())

DATA_FILE = RO_DIRECTORY / "elections" / f"election-{ELECTION_ABBREVIATION}.jsonc"
POSITIONS_FILE = RO_DIRECTORY / "positions" / "positions.json"
RESTRICTIONS_FILE = RO_DIRECTORY / "sjc-restrictions.json"
DESCRIPTIONS_DIR = RO_DIRECTORY / "positions" / "descriptions"
CANDIDATE_FILE = RO_DIRECTORY / "elections" / f"candidates-{ELECTION_ABBREVIATION}.json"
if not os.path.exists(CANDIDATE_FILE):
    CANDIDATE_FILE = None  # pyright: ignore[reportConstantRedefinition]
CANDIDATE_FOLDER = RO_DIRECTORY / "elections" / f"{ELECTION_ABBREVIATION}-candidates"
if not os.path.exists(CANDIDATE_FOLDER):
    CANDIDATE_FOLDER = None  # pyright: ignore[reportConstantRedefinition]


def setup():
    # Complain to the user if DATA_FILE does not exist
    if not os.path.exists(DATA_FILE):
        raise Exception(f"Election data file does not exist (should be at {DATA_FILE})")

    # Ensure output directories exists
    os.makedirs(RO_DIRECTORY / "output" / ELECTION_ABBREVIATION, exist_ok=True)
    os.makedirs(RO_DIRECTORY / "latex-out" / ELECTION_ABBREVIATION, exist_ok=True)

    # Create symlinks
    try:
        # if candidate folder exists, symlink to it
        if CANDIDATE_FOLDER is not None:
            os.symlink(
                CANDIDATE_FOLDER,
                RO_DIRECTORY
                / "latex-out"
                / ELECTION_ABBREVIATION
                / ELECTION_ABBREVIATION,
                target_is_directory=True,
            )
    except FileExistsError:
        print("Candidate folder symlink already exists (this is fine)")

    # Symlink to the logo and class
    for file_name in ["logo.png", "header-footer.cls"]:
        try:
            os.symlink(
                RO_DIRECTORY / "latex-templates" / file_name,
                RO_DIRECTORY / "latex-out" / ELECTION_ABBREVIATION / file_name,
            )
        except FileExistsError:
            print(
                f"Latex template file {file_name} symlink already exists (this is fine)"
            )


def checker(keys: list[str]) -> Callable[[ElectionDataWithStrings], bool]:
    def inner(data: ElectionDataWithStrings) -> bool:
        as_dict = asdict(data)
        return all(as_dict[key] is not None for key in keys)

    return inner


def main():
    election_data = parse_data_from_paths(
        DATA_FILE,
        POSITIONS_FILE,
        RESTRICTIONS_FILE,
        DESCRIPTIONS_DIR,
        CANDIDATE_FILE,
        ELECTION_ABBREVIATION,
    )
    for template in create_templates(RO_DIRECTORY, ELECTION_ABBREVIATION):
        if election_data.type in template.elections:
            try:
                success = write_template_if_have_data(
                    election_data,
                    template.input_location,
                    template.output_location,
                    can_fill_checker=checker(template.required_values),
                    overwrite=True,
                    use_latex_strings=template.is_latex,
                )
                if not success:
                    print(
                        f"Skipped: {template.input_location.name if isinstance(template.input_location, Path) else template.input_location}"
                    )
                else:
                    print(f"Created: {template.output_location}")
            except (
                FileExistsError
            ) as e:  # Won't happen due to True above for overwrite, but just in case
                print(f"File already exists: {e}")


if __name__ == "__main__":
    setup()
    main()
