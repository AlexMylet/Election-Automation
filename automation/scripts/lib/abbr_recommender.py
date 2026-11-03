from data_model import ElectionType, Term

from typing import Optional


def suggest_abbr_data(current_abbr: str) -> tuple[Term, int, ElectionType, Optional[int]]:
    # TODO - compute this
    return ("Michaelmas", 2026, "exec", None)
