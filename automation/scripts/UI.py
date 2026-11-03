import datetime
from enum import Enum, auto
import os
from pathlib import Path
import subprocess
from typing import Any, Callable, Optional
import webbrowser

import customtkinter as ctk
import json

# from automation.scripts import data_filler
from lib.abbr_recommender import suggest_abbr_data
from data_model import ElectionType, Term
from election_abbr import get_election_abbreviation, write_election_abbreviation
from showinfm import show_in_file_manager

NoDataButtonData = tuple[str, Callable[[], Any]]


class TextWithButtonsFrame(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTk | ctk.CTkFrame,
        text: str,
        buttons_data: list[NoDataButtonData],
    ):
        super().__init__(master)

        self.text = ctk.CTkLabel(self, text=text)
        self.text.grid(row=0, column=0, padx=20, pady=20)
        self.buttons: list[ctk.CTkButton] = []
        for i, button_data in enumerate(buttons_data):
            self.buttons.append(
                ctk.CTkButton(self, text=button_data[0], command=button_data[1])
            )
            self.buttons[i].grid(row=0, column=i + 1, padx=20, pady=20)

    def update_text(self, new_text: str):
        self.text.configure(text=new_text)


class ElectionAbbrBuilderFrame(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTk | ctk.CTkFrame,
        current: str,
        suggested_term: Term,
        suggested_year: int,
        suggested_type: ElectionType,
        suggested_by_election_number: Optional[int],
        update_callback: Callable[[str], Any],
        abbr_display_callback: Callable[[str], Any],
    ):
        super().__init__(master)

        self.term: Term = suggested_term
        self.year = suggested_year
        self.type: ElectionType = suggested_type
        self.by_number = suggested_by_election_number

        self.on_update_abbr = abbr_display_callback
        self.update_callback = update_callback

        self.build_abbr()

        # TODO - maybe call suggest_abbr_data from here, rather than the caller?

        self.term_selection = ctk.CTkOptionMenu(
            self, values=["Michaelmas", "Hilary", "Trinity"], command=self.term_update
        )
        self.term_selection.set(self.term)
        self.term_selection.grid(row=0, column=0, padx=20, pady=20)

        self.year_enter = ctk.CTkTextbox(self, width=100)
        self.year_enter.bind(command=self.year_update)
        self.year_enter.insert("0.0", str(self.year))
        self.year_enter.grid(row=0, column=1, padx=20, pady=20)

        self.election_type_selection = ctk.CTkOptionMenu(
            self,
            values=["Executive", "General", "By-election"],
            command=self.type_update,
        )
        match self.type:
            case "by-election":
                self.election_type_selection.set("By-election")
            case "exec":
                self.election_type_selection.set("Executive")
            case "general":
                self.election_type_selection.set("General")
        self.election_type_selection.grid(row=0, column=2, padx=20, pady=20)

        self.by_number_enter = ctk.CTkTextbox(self, width=50)
        self.by_number_enter.bind(command=self.by_number_update)
        if self.by_number is not None:
            self.by_number_enter.insert("0.0", str(self.by_number))
        self.by_number_enter.grid(row=0, column=3, padx=20, pady=20)
        if self.type != "by-election":
            self.by_number_enter.configure(state="disabled")

    def term_update(self, term: str):
        self.term = term  # type: ignore
        self.build_abbr_and_display()

    def year_update(self, year: str):
        try:
            self.year = int(year)
        except TypeError:
            pass
        self.build_abbr_and_display()

    def type_update(self, type: str):
        match type:
            case "Executive":
                self.type = "exec"
            case "General":
                self.type = "general"
            case "By-election":
                self.type = "by-election"
            case _:
                raise ValueError("Should be unreachable")
        self.build_abbr_and_display()

    def by_number_update(self, number: str):
        self.by_number = number
        self.build_abbr_and_display()

    def build_abbr_and_display(self):
        self.new_abbr = self.build_abbr()
        self.on_update_abbr(self.new_abbr)

    def build_abbr(self) -> str:
        term_letter = self.term[0]
        type_letter = self.type[0].upper()
        by_str = f"-{self.by_number}" if self.type == "by-election" else ""

        return f"{term_letter}T{self.year % 100:02}-{type_letter}{by_str}"

    def submit(self):
        self.update_callback(self.new_abbr)


class AppState(Enum):
    INITIAL = auto()
    ABBR_UPDATE = auto()


RO_DIRECTORY = Path(os.getcwd())


def check_election_file_existence(current_abbr: str) -> bool:
    try:
        fp = open(RO_DIRECTORY / "elections" / f"election-{current_abbr}.json")
    except OSError:
        return False
    else:
        fp.close()
        return True


def check_candidates_file_existence(current_abbr: str) -> bool:
    try:
        fp = open(RO_DIRECTORY / "elections" / f"candidates-{current_abbr}.json")
    except OSError:
        return False
    else:
        fp.close()
        return True


def check_folder_existence(folder_path: Path) -> bool:
    return folder_path.exists()


def create_election_file_with_sensible_defaults(current_abbr: str) -> None:
    with open(
        RO_DIRECTORY / "elections" / f"election-{current_abbr}.json", "x"
    ) as election_file:
        print("Election file created")
    with open(
        RO_DIRECTORY / "elections" / f"election-{current_abbr}.json", "w"
    ) as election_file:
        election_number = None
        match current_abbr[5]:
            case "E":
                election_type = "exec"
            case "G":
                election_type = "general"
            case "B":
                election_type = "by-election"
                election_number = int(current_abbr[7:])
            case _:
                raise ValueError("Invalid election abbr")

        match current_abbr[0]:
            case "M":
                election_term = "Michaelmas"
            case "H":
                election_term = "Hilary"
            case "T":
                election_term = "Trinity"
            case _:
                raise ValueError("Invalid election abbr")

        year_mod_100 = int(current_abbr[2:4])
        current_year = datetime.date.today().year
        # Least year after current year with year_mod_100 as the year_mod_100
        if current_year % 100 <= year_mod_100:
            election_year = (current_year // 100) * 100 + year_mod_100
        else:
            election_year = (current_year // 100) * 100 + year_mod_100 + 100

        data: dict[str, Any] = {
            "roName": "[Add your name here]",
            "type": election_type,
            "term": election_term,
            "year": election_year,
        }
        if election_number is not None:
            data["number"] = election_number

        json.dump(data, election_file, indent=4)


def create_candidates_file_with_sensible_defaults(current_abbr: str) -> None:
    with open(
        RO_DIRECTORY / "elections" / f"candidates-{current_abbr}.json", "x"
    ) as candidates_file:
        print("Candidates file created")
    with open(
        RO_DIRECTORY / "elections" / f"candidates-{current_abbr}.json", "w"
    ) as candidates_file:
        data = []
        json.dump(data, candidates_file, indent=4)


class OpenTool(Enum):
    WEBBROWSER = auto()
    VSCODE = auto()


def open_or_create_and_open(
    current_abbr: str, election_file_exists: bool, tool: OpenTool
) -> None:
    if not election_file_exists:
        create_election_file_with_sensible_defaults(current_abbr)
        # TODO - update the UI to reflect the fact that the file now exists
    file_path = str(RO_DIRECTORY / "elections" / f"election-{current_abbr}.json")
    if tool == OpenTool.WEBBROWSER:
        # With thanks to Gemini
        webbrowser.open(file_path)
    elif tool == OpenTool.VSCODE:
        subprocess.run(["code", file_path])


def open_or_create_and_open_folder(path: Path, folder_exists: bool) -> None:
    if not folder_exists:
        # Create
        os.makedirs(path)
        # TODO - Update UI

    show_in_file_manager(str(path))


def open_or_create_and_open_candidates(
    current_abbr: str, candidates_file_exists: bool, tool: OpenTool
) -> None:
    if not candidates_file_exists:
        create_candidates_file_with_sensible_defaults(current_abbr)
        # TODO - update the UI to reflect the fact that the file now exists
    file_path = str(RO_DIRECTORY / "elections" / f"candidates-{current_abbr}.json")
    if tool == OpenTool.WEBBROWSER:
        # With thanks to Gemini
        webbrowser.open(file_path)
    elif tool == OpenTool.VSCODE:
        subprocess.run(["code", file_path])


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.app_state = AppState.INITIAL
        self.elements = []

        self.title("Election Automation")
        self.geometry("1000x600")
        self.main_page_setup()

        self.state_transitions: dict[tuple[AppState, AppState], Callable[[], None]] = {
            (AppState.INITIAL, AppState.ABBR_UPDATE): self.initial_to_abbr_update,
            (AppState.ABBR_UPDATE, AppState.INITIAL): self.main_page_setup,
        }

    def clear_window(self):
        for element in self.elements:
            element.grid_forget()
        self.elements = []

    def main_page_setup(self):
        self.clear_window()
        self.election_abbreviation = TextWithButtonsFrame(
            self,
            f"Current Election Abbreviation: '{get_election_abbreviation()}'.",
            [("Update", lambda: self.update_state(AppState.ABBR_UPDATE))],
        )
        self.election_abbreviation.grid(row=0, column=0, padx=20, pady=20)

        election_file_exists = check_election_file_existence(
            get_election_abbreviation()
        )
        self.election_file = TextWithButtonsFrame(
            self,
            f"election-{get_election_abbreviation()}.json",
            [
                (
                    (
                        "Open (for editing, using system default for JSON files)"
                        if election_file_exists
                        else "Create election file with sensible defaults and edit"
                    ),
                    lambda: open_or_create_and_open(
                        get_election_abbreviation(),
                        election_file_exists,
                        OpenTool.WEBBROWSER,
                    ),
                ),
                (
                    (
                        "Open (for editing, using VS Code)"
                        if election_file_exists
                        else "Create election file with sensible defaults and edit"
                    ),
                    lambda: open_or_create_and_open(
                        get_election_abbreviation(),
                        election_file_exists,
                        OpenTool.VSCODE,
                    ),
                ),
            ],
        )
        self.election_file.grid(row=1, column=0, padx=20, pady=20)

        candidates_folder_name = lambda: f"{get_election_abbreviation()}-candidates"
        candidates_folder_exists = check_folder_existence(
            RO_DIRECTORY / "elections" / candidates_folder_name()
        )

        self.candidates_folder = TextWithButtonsFrame(
            self,
            candidates_folder_name(),
            [
                (
                    (
                        "Open folder"
                        if candidates_folder_exists
                        else "Create and open folder"
                    ),
                    lambda: open_or_create_and_open_folder(
                        RO_DIRECTORY / "elections" / candidates_folder_name(),
                        candidates_folder_exists,
                    ),
                )
            ],
        )
        self.candidates_folder.grid(row=2, column=0, padx=20, pady=20)

        candidates_file_name = lambda: f"candidates-{get_election_abbreviation()}.json"
        candidates_file_exists = check_candidates_file_existence(
            get_election_abbreviation()
        )

        self.candidates_file = TextWithButtonsFrame(
            self,
            candidates_file_name(),
            [
                (
                    (
                        "Open (for editing, using system default for JSON files)"
                        if candidates_file_exists
                        else "Create election file with sensible defaults and edit"
                    ),
                    lambda: open_or_create_and_open_candidates(
                        get_election_abbreviation(),
                        candidates_file_exists,
                        OpenTool.WEBBROWSER,
                    ),
                ),
                (
                    (
                        "Open (for editing, using VS Code)"
                        if election_file_exists
                        else "Create election file with sensible defaults and edit"
                    ),
                    lambda: open_or_create_and_open_candidates(
                        get_election_abbreviation(),
                        candidates_file_exists,
                        OpenTool.VSCODE,
                    ),
                ),
            ],
        )
        self.candidates_file.grid(row=3, column=0, padx=20, pady=20)

        self.button = ctk.CTkButton(self, text="submit", command=self.button_callback)
        self.button.grid(row=4, column=0, padx=20, pady=20)

        self.elements: list[ctk.CTkBaseClass] = [
            self.election_abbreviation,
            self.election_file,
            self.candidates_folder,
            self.candidates_file,
            self.button,
        ]

    def update_state(self, intended_state: AppState) -> bool:
        transition = self.state_transitions.get((self.app_state, intended_state), None)
        if transition is None:
            return False
        else:
            transition()
            self.app_state = intended_state
            return True

    def button_callback(self):
        print("button clicked")

    def initial_to_abbr_update(self) -> None:
        self.clear_window()

        self.current_display = TextWithButtonsFrame(
            self,
            f"Current abbr: {get_election_abbreviation()}",
            [("Keep this", lambda: self.update_state(AppState.INITIAL))],
        )
        self.current_display.grid(row=0, column=0, padx=20, pady=20)

        def display_update(x: str):
            return self.new_with_submit.update_text(x)

        suggested_term, suggested_year, suggested_type, suggested_by_election_number = (
            suggest_abbr_data(get_election_abbreviation())
        )
        self.election_abbreviation_updater = ElectionAbbrBuilderFrame(
            self,
            get_election_abbreviation(),
            suggested_term,
            suggested_year,
            suggested_type,
            suggested_by_election_number,
            self.update_election_abbr,
            display_update,
        )
        self.election_abbreviation_updater.grid(row=1, column=0, padx=20, pady=20)

        self.new_with_submit = TextWithButtonsFrame(
            self, "Placeholder", [("update", self.election_abbreviation_updater.submit)]
        )
        self.new_with_submit.grid(row=2, column=0, padx=20, pady=20)

        self.election_abbreviation_updater.build_abbr_and_display()

        self.elements = [
            self.current_display,
            self.election_abbreviation_updater,
            self.new_with_submit,
        ]

    def update_election_abbr(self, election_abbr: str) -> None:
        # Write-to-file
        if election_abbr != get_election_abbreviation():
            write_election_abbreviation(election_abbr)

        self.update_state(AppState.INITIAL)


app = App()
app.mainloop()
