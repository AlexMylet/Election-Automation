from dataclasses import dataclass
from typing import Literal, Optional

# Assumptions: that templates can use:
# 1. We have at least one position in the election (enforced by schema) (or from exec/non-exec)
# 2. We have at least one restriction that is in effect (enforced by hating the Oxford Union)

Term = Literal["Michaelmas", "Hilary", "Trinity"]
ElectionType = Literal["exec", "general", "by-election"]


@dataclass
class Position:
    id: str
    full_name: str
    description: list[
        str
    ]  # Each line is a latex command for doing that bullet point in latex
    su_platform_name: str
    is_exec: bool = False
    position_count: int = 1


@dataclass
class Restriction:
    id: str
    text: str
    constitution_reference: str
    rule_type: Literal[
        "multiple_positions", "exec", "all", "specific_roles", "trinity-by"
    ]
    positions: Optional[list[Position]]


@dataclass
class Time:
    day: Literal[
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "today",
        "tomorrow",
    ]
    time: Optional[str]
    week: Optional[int]


@dataclass
class Candidate:
    position: Position
    full_name: str
    mobile_number: str
    manifesto_name: str
    latex_manifesto_name: str
    email: str
    photo_file_name: str
    manifesto_latex_file_name: str
    manifesto_text_file_name: str
    manifesto_files_path: str
    eligible: bool
    multiple_people: bool
    extra_emails: list[str]


@dataclass
class ElectionData:
    ro_name: str
    positions: list[Position]
    general_election_executive_by_elected_positions: list[Position]
    restrictions: list[Restriction]
    type: ElectionType
    term: Term
    year: int
    committee_year: str
    nominations_open_time: Optional[Time]
    nominations_deadline_time: Optional[Time]
    manifestos_release_time: Optional[Time]
    hustings_time: Optional[Time]
    polls_open: Optional[Time]
    polls_close: Optional[Time]
    hustings_location: Optional[str]
    candidates: Optional[list[Candidate]]
    justification: Optional[str]
    by_election_number: Optional[int]
    role_by_election_number: Optional[Literal[1, 2]]


@dataclass
class ElectionDataWithStrings(ElectionData):
    positions_string: str
    positions_plural_s: str
    positions_is_are: str
    positions_this_these: str
    term_first_letter: str
    padded_year_mod_100: str
    space_plus_by_election_number: str
    """If not a by-election, empty.
    If by-election 1, empty."""
    non_by_election_n: str
    by_plus_dash: str
    election_type: str
    one_of_restrictions: str
    restrictions_plural_s: str
    second_plus_space: str
    positions_with_candidates: Optional[list[tuple[Position, list[Candidate]]]]
    """includes only those positions with candidates"""
    positions_without_candidates: Optional[list[Position]]
    positions_without_candidates_plural_s: Optional[str]
    positions_general_exec_by_plural_s: Optional[str]
    positions_general_exec_by_is_are: Optional[str]
    positions_general_exec_by_an_e: Optional[str]
