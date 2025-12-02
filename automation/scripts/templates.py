from pathlib import Path
from typing import NamedTuple

from data_model import ElectionType

ALL_ELECTIONS: list[ElectionType] = [
    "general",
    "by-election",
    "exec",
]


class TemplateData(NamedTuple):
    input_location: str | Path
    output_location: str | Path
    required_values: list[str]
    """Values which are Optional in the type ElectionDataWithStrings
    but that need to be present for the template to succeed"""
    elections: list[ElectionType]
    """Which elections this template is valid for"""
    is_latex: bool = False


def create_templates(
    RO_DIRECTORY: Path, ELECTION_ABBREVIATION: str
) -> list[TemplateData]:
    return [
        # Announcement
        TemplateData(
            RO_DIRECTORY / "email-templates" / "general-announce.txt",
            RO_DIRECTORY / "output" / ELECTION_ABBREVIATION / "announce.txt",
            [
                "nominations_open_time",
                "nominations_deadline_time",
                "manifestos_release_time",
                "hustings_time",
                "polls_open",
            ],
            ["general"],
        ),
        TemplateData(
            RO_DIRECTORY / "email-templates" / "executive-announce.txt",
            RO_DIRECTORY / "output" / ELECTION_ABBREVIATION / "announce.txt",
            [
                "nominations_open_time",
                "nominations_deadline_time",
                "manifestos_release_time",
                "hustings_time",
                "polls_open",
            ],
            ["exec"],
        ),
        TemplateData(
            RO_DIRECTORY / "email-templates" / "byelection-announce.txt",
            RO_DIRECTORY / "output" / ELECTION_ABBREVIATION / "announce.txt",
            [
                "nominations_deadline_time",
                "manifestos_release_time",
                "hustings_time",
                "polls_open",
                "justification",
            ],
            ["by-election"],
        ),
        TemplateData(
            RO_DIRECTORY / "latex-templates" / "role-descriptions-template.tex",
            RO_DIRECTORY
            / "latex-out"
            / ELECTION_ABBREVIATION
            / f"positions-{ELECTION_ABBREVIATION}.tex",
            [],
            ALL_ELECTIONS,
            True,
        ),
        TemplateData(
            RO_DIRECTORY / "other-templates" / "instructions-for-nominations-form.txt",
            RO_DIRECTORY
            / "output"
            / ELECTION_ABBREVIATION
            / f"instructions-for-nominations-form.txt",
            [],
            ALL_ELECTIONS,
        ),
        TemplateData(
            RO_DIRECTORY / "latex-templates" / "manifestos-template.tex",
            RO_DIRECTORY
            / "latex-out"
            / ELECTION_ABBREVIATION
            / f"candidates-{ELECTION_ABBREVIATION}.tex",
            ["candidates"],
            ALL_ELECTIONS,
            True,
        ),
        TemplateData(
            RO_DIRECTORY / "latex-templates" / "notice-of-poll-template.tex",
            RO_DIRECTORY
            / "latex-out"
            / ELECTION_ABBREVIATION
            / f"notice-of-poll-{ELECTION_ABBREVIATION}.tex",
            ["polls_open", "polls_close"],
            ALL_ELECTIONS,
            True,
        ),
        TemplateData(
            RO_DIRECTORY / "email-templates" / "manifestos.txt",
            RO_DIRECTORY / "output" / ELECTION_ABBREVIATION / "manifestos.txt",
            [
                "positions_with_candidates",
                "hustings_time",
                "polls_open",
                "hustings_location",
            ],
            ALL_ELECTIONS,
            False,
        ),
        TemplateData(
            RO_DIRECTORY / "other-templates" / "instructions-for-filling-in-su.txt",
            RO_DIRECTORY / "output" / ELECTION_ABBREVIATION / "su-platform.txt",
            ["positions_with_candidates"],
            ALL_ELECTIONS,
            False,
        ),
        TemplateData(
            RO_DIRECTORY
            / "other-templates"
            / "instructions-for-creating-election-in-su.txt",
            RO_DIRECTORY / "output" / ELECTION_ABBREVIATION / "su-creation.txt",
            ["polls_open", "polls_close"],
            ALL_ELECTIONS,
            False,
        ),
        TemplateData(
            RO_DIRECTORY / "email-templates" / "email-list.txt",
            RO_DIRECTORY / "output" / ELECTION_ABBREVIATION / "emails.txt",
            ["positions_with_candidates"],
            ALL_ELECTIONS,
            False,
        ),
    ]
