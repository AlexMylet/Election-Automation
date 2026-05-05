from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any, Callable, Optional

import json5
from data_model import (
    Candidate,
    ElectionDataWithStrings,
    Position,
    Restriction,
    Term,
    Time,
)
from jinja2 import Environment, FileSystemLoader


def parse_all_positions(
    parsed_positions_json: list[dict[str, Any]],
    descriptions_folder_path: str | Path,
) -> list[Position]:
    def parse_position(position: dict[str, Any]) -> Position:
        # Read file
        description: list[str] = []
        with open(Path(descriptions_folder_path) / position["description_file"]) as d:
            for line in d.readlines():
                description.append(line)
        if len(description) == 0:
            description = [""]  # Prevent LaTeX errors

        # Build data
        full_name = position["full_name"]
        return Position(
            id=position["id"],
            full_name=full_name,
            su_platform_name=position.get("su_platform_name", full_name),
            description=description,
            is_exec=position.get("is_exec", False),
            position_count=position.get("position_count", 1),
        )

    return list(map(parse_position, parsed_positions_json))


def parse_positions(
    positions_to_parse: list[str], all_positions: list[Position]
) -> list[Position]:
    res: list[Position] = []
    for id in positions_to_parse:
        for position in all_positions:
            if id == position.id:
                res.append(position)
                break
        else:  # no break
            raise ValueError(
                f"Attempting to use position {id} in election, but the position does not exist."
            )
    return res


def parse_restrictions(
    parsed_restrictions_json: list[dict[str, Any]], all_positions: list[Position]
) -> list[Restriction]:
    res: list[Restriction] = []
    for restriction in parsed_restrictions_json:

        restriction_positions = restriction["rule"].get("roles")
        if restriction_positions is not None:
            restriction_positions_as_objects: list[Position] | None = []

            for id in restriction_positions:
                for position in all_positions:
                    if position.id == id:
                        restriction_positions_as_objects.append(position)
                        break
                else:
                    # If not in, ignore (maybe as not up for election, maybe as not valid)
                    raise ValueError(
                        f"{restriction['id']} claims to apply to position {id}, which does not exist"
                    )

        else:
            restriction_positions_as_objects = None

        res.append(
            Restriction(
                id=restriction["id"],
                text=restriction["text"],
                constitution_reference=restriction["constitution_reference"],
                rule_type=restriction["rule"]["rule_type"],
                positions=restriction_positions_as_objects,
            )
        )

    return res


def restrictions_in_force(
    restrictions: list[Restriction], positions: list[Position], term: Term
) -> list[Restriction]:
    def restriction_holds(restriction: Restriction) -> bool:
        match restriction.rule_type:
            case "multiple_positions":
                return len(positions) > 1
            case "all":
                return True
            case "exec":
                return any(map(lambda pos: pos.is_exec, positions))
            case "trinity-by":
                return term == "Trinity"
            case "specific_roles":
                if restriction.positions is None:
                    raise ValueError(
                        "No roles given for specific roles (you are not checking against the schema)"
                    )
                # Do to how we strip positions not up for election,
                # we could do
                # return len(restriction.positions) > 0
                # But, in case we change the above, we don't
                for position in positions:
                    for role in restriction.positions:
                        if role == position:
                            return True
                return False

    return list(filter(restriction_holds, restrictions))


def time_dict_to_time_object(time: dict[str, Any] | None) -> Time | None:
    if time is None:
        return None
    return Time(
        day=time["day"], week=time.get("week", None), time=time.get("time", None)
    )


def parse_candidates(
    positions: list[Position],
    candidates: list[dict[str, Any]] | None,
    path_string: str | None,
) -> list[Candidate] | None:
    if candidates is None or path_string is None:
        return None
    res: list[Candidate] = []
    for candidate in candidates:
        try:
            position = next(
                pos for pos in positions if pos.id == candidate["position_id"]
            )
            res.append(
                Candidate(
                    position=position,
                    full_name=candidate["name"],
                    mobile_number=candidate["mobileNumber"],
                    manifesto_name=candidate["manifestoName"],
                    latex_manifesto_name=candidate.get(
                        "latexSafeManifestoName", candidate["manifestoName"]
                    ),
                    email=candidate["email"],
                    photo_file_name=candidate["photoFileName"],
                    manifesto_latex_file_name=candidate["manifestoLatexFileName"],
                    manifesto_text_file_name=candidate["manifestoTextFileName"],
                    manifesto_files_path=path_string,
                    eligible=candidate.get("eligible", True),
                    multiple_people=candidate.get("multiplePeople", False),
                    extra_emails=candidate.get("extraEmails", []),
                )
            )
        except StopIteration:
            raise ValueError(
                "Candidate applying for position that is not up for election."
            )

    return res


def parse_data(
    parsed_election_json: Any,
    parsed_positions_json: list[dict[str, Any]],
    parsed_restrictions_json: list[dict[str, Any]],
    parsed_candidates_data: Optional[list[dict[str, Any]]],
    candidates_path_string: Optional[str],
    descriptions_folder_path: str | Path,
) -> ElectionDataWithStrings:

    election_type = parsed_election_json["type"]
    is_by_election = election_type == "by-election"
    all_positions = parse_all_positions(parsed_positions_json, descriptions_folder_path)
    if is_by_election:
        by_elected_positions = []
        positions = parse_positions(parsed_election_json["positions"], all_positions)
    elif election_type == "exec":
        by_elected_positions = []
        positions = list(filter(lambda p: p.is_exec, all_positions))
    else:
        assert election_type == "general"
        # TODO - allow Executive by-election too (by listed positions)
        by_elected_positions = parse_positions(
            parsed_election_json.get("positions", []), all_positions
        )
        for position in by_elected_positions:
            if not position.is_exec:
                print(
                    f"Warning: position {position.full_name} is up for general by-election but is"
                    + "not an executive position (so will appear twice)"
                )
        positions = list(filter(lambda p: not p.is_exec, all_positions))

    positions_string = (
        positions[0].full_name
        if len(positions) == 1
        else ", ".join(map(lambda p: p.full_name, positions[:-1]))
        + " and "
        + positions[-1].full_name
    )

    term = parsed_election_json["term"]
    year = parsed_election_json.get("year", date.today().year)

    restrictions = parse_restrictions(parsed_restrictions_json, all_positions)

    in_force_restrictions = restrictions_in_force(
        restrictions, positions + by_elected_positions, term
    )

    candidates = parse_candidates(
        positions + by_elected_positions, parsed_candidates_data, candidates_path_string
    )
    by_election_number = parsed_election_json.get("number")

    role_by_election_number = parsed_election_json.get("roleByElectionNumber")

    if candidates is None:
        positions_with_candidates = None
        positions_without_candidates = None
    else:
        possibly_empty = list(
            map(
                (
                    lambda p: (
                        p,
                        list(filter(lambda c: c.position == p, candidates)),
                    )
                ),
                by_elected_positions + positions,
            )
        )
        positions_with_candidates = list(
            filter(lambda pcs: pcs[1] != [], possibly_empty)
        )
        positions_without_candidates = list(
            filter(lambda pcs: pcs[1] == [], possibly_empty)
        )
        positions_without_candidates = list(
            map(lambda pcs: pcs[0], positions_without_candidates)
        )

    return ElectionDataWithStrings(
        ro_name=parsed_election_json["roName"],
        positions=positions,
        general_election_executive_by_elected_positions=by_elected_positions,
        restrictions=in_force_restrictions,
        type=election_type,
        term=term,
        year=year,
        committee_year=parsed_election_json.get(
            "committeeYear", year if is_by_election else year + 1
        ),
        nominations_open_time=time_dict_to_time_object(
            parsed_election_json.get("nominationsOpen")
        ),
        nominations_deadline_time=time_dict_to_time_object(
            parsed_election_json.get("nominationsDeadline")
        ),
        manifestos_release_time=time_dict_to_time_object(
            parsed_election_json.get("manifestoReleaseTime")
        ),
        hustings_time=time_dict_to_time_object(
            parsed_election_json.get("hustingsTime")
        ),
        polls_open=time_dict_to_time_object(parsed_election_json.get("electionStart")),
        polls_close=time_dict_to_time_object(parsed_election_json.get("electionEnd")),
        hustings_location=parsed_election_json.get("hustingsLocation"),
        candidates=candidates,
        justification=parsed_election_json.get("justification"),
        by_election_number=by_election_number,
        role_by_election_number=role_by_election_number,
        positions_string=positions_string,
        positions_plural_s="s" if len(positions) > 1 else "",
        positions_is_are="are" if len(positions) > 1 else "is",
        positions_this_these="these" if len(positions) > 1 else "this",
        term_first_letter=parsed_election_json["term"][0],
        padded_year_mod_100=f"{year % 100:02d}",
        space_plus_by_election_number=(
            f" {by_election_number}"
            if by_election_number is not None and by_election_number > 1
            else ""
        ),
        non_by_election_n="n" if not is_by_election else "",
        by_plus_dash="by-" if is_by_election else "",
        election_type=(
            "By-"
            if is_by_election
            else ("Executive " if election_type == "exec" else "General ")
        ),
        one_of_restrictions="one of " if len(in_force_restrictions) > 1 else "",
        restrictions_plural_s="s" if len(in_force_restrictions) > 1 else "",
        second_plus_space="second " if role_by_election_number == 2 else "",
        positions_with_candidates=positions_with_candidates,
        positions_without_candidates=positions_without_candidates,
        positions_without_candidates_plural_s=(
            None
            if positions_without_candidates is None
            else "s" if len(positions_without_candidates) > 1 else ""
        ),
        positions_general_exec_by_plural_s=(
            "s"
            if len(by_elected_positions) > 1
            else ("" if len(by_elected_positions) == 1 else None)
        ),
        positions_general_exec_by_is_are=(
            "are"
            if len(by_elected_positions) > 1
            else ("is" if len(by_elected_positions) == 1 else None)
        ),
        positions_general_exec_by_an_e=(
            "E"
            if len(by_elected_positions) > 1
            else ("An e" if len(by_elected_positions) == 1 else None)
        ),
    )


def parse_data_from_paths(
    election_json_path: str | Path,
    positions_json_path: str | Path,
    restrictions_json_path: str | Path,
    descriptions_folder_path: str | Path,
    candidates_json_path: Optional[str | Path],
    candidate_path_string: Optional[str],
) -> ElectionDataWithStrings:
    with (
        open(election_json_path) as election_file,
        open(positions_json_path) as positions_file,
        open(restrictions_json_path) as restrictions_file,
    ):
        election_data = json5.load(  # pyright: ignore[reportUnknownMemberType]
            election_file
        )
        positions_data = json5.load(  # pyright: ignore[reportUnknownMemberType]
            positions_file
        )
        restrictions_data = json5.load(  # pyright: ignore[reportUnknownMemberType]
            restrictions_file
        )
        if candidates_json_path is not None:
            with open(candidates_json_path) as candidates_file:
                candidates_data = (
                    json5.load(  # pyright: ignore[reportUnknownMemberType]
                        candidates_file
                    )
                )
        else:
            candidates_data = None

        return parse_data(
            election_data,
            positions_data,
            restrictions_data,
            candidates_data,
            candidate_path_string,
            descriptions_folder_path,
        )


def write_template_if_have_data(
    election_data: ElectionDataWithStrings,
    template_path: str | Path,
    output_path: str | Path,
    *,
    can_fill_checker: Optional[Callable[[ElectionDataWithStrings], bool]] = None,
    overwrite: bool = False,
    use_latex_strings: bool = False,
) -> bool:
    if can_fill_checker is not None and not can_fill_checker(election_data):
        return False

    if use_latex_strings:
        environment = Environment(
            loader=FileSystemLoader("/"),
            block_start_string="%<|",
            block_end_string="|>%",
            variable_start_string="$<{",
            variable_end_string="}>$",
        )
    else:
        environment = Environment(
            loader=FileSystemLoader("/"),
        )
    template = environment.get_template(str(template_path))
    output = template.render(asdict(election_data))

    with open(output_path, "w" if overwrite else "x") as output_file:
        output_file.write(output)
    return True


def parse_data_and_write(
    election_json_path: str | Path,
    positions_json_path: str | Path,
    restrictions_json_path: str | Path,
    descriptions_folder_path: str | Path,
    candidates_json_path: Optional[str | Path],
    candidate_path_string: Optional[str],
    template_path: str | Path,
    output_path: str | Path,
    *,
    can_fill_checker: Optional[Callable[[ElectionDataWithStrings], bool]] = None,
    overwrite: bool = False,
    use_latex_strings: bool = False,
) -> bool:
    """Parse data from files, and write template with this data to output_path.

    If can fill checker is provided and returns False on the passed data, return False
    (and don't write).

    If overwrite is True, overwrite existing file.
    If overwrite is False and file exists, the FileExistsError from open(output_path, "x")
    is not caught (i.e., thrown to you).
    """
    needed_data = parse_data_from_paths(
        election_json_path,
        positions_json_path,
        restrictions_json_path,
        descriptions_folder_path,
        candidates_json_path,
        candidate_path_string,
    )
    return write_template_if_have_data(
        needed_data,
        template_path,
        output_path,
        can_fill_checker=can_fill_checker,
        overwrite=overwrite,
        use_latex_strings=use_latex_strings,
    )
