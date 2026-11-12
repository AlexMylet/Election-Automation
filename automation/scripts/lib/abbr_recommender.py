import datetime
from typing import Optional

from data_model import ElectionType, Term


def suggest_abbr_data(current_abbr: str) -> tuple[Term, int, ElectionType, Optional[int]]:
    # Term and year based off current date
    today = datetime.datetime.now().date()
    trinity_threshold = (1, 4)
    michaelmas_threshold = (1, 9)
    hilary_threshold = (9, 12)
    if today.month > trinity_threshold[1] or (today.month == trinity_threshold[1] and today.day >= trinity_threshold[0]):
        if today.month > michaelmas_threshold[1] or (today.month == michaelmas_threshold[1] and today.day >= michaelmas_threshold[0]):
            if today.month > hilary_threshold[1] or (today.month == hilary_threshold[1] and today.day >= hilary_threshold[0]):
                # Hilary of next year
                term = "Hilary"
                year = today.year + 1
            else:
                # Michalemas of this year
                term = "Michaelmas"
                year = today.year
        else:
            # Trinity of this year
            term = "Trinity"
            year = today.year
    else:
        # Hilary of this year
        term = "Hilary"
        year = today.year

    if f"{term[0]}T{year % 100}" == current_abbr[:4]:
        # next election here
        match current_abbr[5]:
            case "E":
                type = "general"
                by_number = None
            case "G":
                type = "by-election"
                by_number = 1
            case "B":
                type = "by-election"
                by_number = int(current_abbr[7:]) + 1
            case _:
                type = "exec"
                by_number = None
    else:
        if term == "Michaelmas":
            type = "exec"
            by_number = None
        else:
            type = "by-election"
            by_number = 1

    return (term, year, type, by_number)
