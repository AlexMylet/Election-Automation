import datetime
import os
import subprocess
import webbrowser
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Optional

import customtkinter as ctk
import data_filler
from data_model import ElectionType, Term
from election_abbr import get_election_abbreviation, write_election_abbreviation
from lib.abbr_recommender import suggest_abbr_data
from lib.file_handling import (
    check_file_existence,
    create_file_and_write_json,
)
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
            new_button = ctk.CTkButton(
                self, text=button_data[0], command=button_data[1]
            )
            self.buttons.append(new_button)
            new_button.grid(row=0, column=i + 1, padx=20, pady=20)

    def update_text(self, new_text: str):
        self.text.configure(text=new_text)

    def update_buttons_text(self, new_texts: list[str]):
        for button, new_text in zip(self.buttons, new_texts):
            button.configure(text=new_text)


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
    return check_file_existence(
        RO_DIRECTORY / "elections" / f"election-{current_abbr}.json"
    )


def check_candidates_file_existence(current_abbr: str) -> bool:
    return check_file_existence(
        RO_DIRECTORY / "elections" / f"candidates-{current_abbr}.json"
    )


def check_folder_existence(folder_path: Path) -> bool:
    return folder_path.exists()


def elections_file_path(abbr: str):
    return RO_DIRECTORY / "elections" / f"election-{abbr}.json"


@create_file_and_write_json(elections_file_path)
def create_election_file_with_sensible_defaults(current_abbr: str) -> dict[str, Any]:
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
    if election_type == "by-election":
        data["positions"] = []
    return data


def candidates_file_path(abbr: str):
    return RO_DIRECTORY / "elections" / f"candidates-{abbr}.json"


@create_file_and_write_json(candidates_file_path)
def create_candidates_file_with_sensible_defaults(current_abbr: str) -> list[Any]:
    return []


class FileOpenTool(Enum):
    WEBBROWSER = auto()
    VSCODE = auto()


def open_or_create_and_open_file(
    current_abbr: str,
    path: Path,
    tool: FileOpenTool,
    election_abbr_based_default_file_creator: Callable[[str], None],
    on_file_creation: Optional[Callable[[], None]] = None,
) -> None:
    if not check_file_existence(path):
        election_abbr_based_default_file_creator(current_abbr)
        if on_file_creation is not None:
            on_file_creation()
    file_path = str(path)
    if tool == FileOpenTool.WEBBROWSER:
        # With thanks to Gemini
        webbrowser.open(file_path)
    elif tool == FileOpenTool.VSCODE:
        subprocess.run(["code", file_path])


def open_or_create_and_open_folder(
    path: Path,
    on_folder_creation: Optional[Callable[[], None]] = None,
) -> None:
    if not check_folder_existence(path):
        # Create
        os.makedirs(path)
        if on_folder_creation is not None:
            on_folder_creation()

    show_in_file_manager(str(path))


def create_text_with_button_frames_for_file_opening(
    master: ctk.CTk | ctk.CTkFrame,
    file_name: Callable[[], str],
    path_generator: Callable[[str], Path],
    type_of_file: str,
    file_creator: Callable[[str], None],
) -> TextWithButtonsFrame:
    path = path_generator(get_election_abbreviation())
    file_exists = check_file_existence(path)

    def open_or_create_and_open_file_lambda(toolValue: int):
        def inner():
            open_or_create_and_open_file(
                get_election_abbreviation(),
                path_generator(get_election_abbreviation()),
                FileOpenTool(toolValue),
                file_creator,
                frame.update_buttons_text(
                    [
                        f"Open {type_of_file} (using {description})"
                        for description in ["System Default", "VS Code"]
                    ]
                ),
            )

        return inner

    frame = TextWithButtonsFrame(
        master,
        file_name(),
        [
            (
                (
                    f"Open {type_of_file} (using {description})"
                    if file_exists
                    else f"Create {type_of_file} with sensible defaults and open (using {description})"
                ),
                open_or_create_and_open_file_lambda(tool.value),
            )
            for tool, description in [
                (FileOpenTool.WEBBROWSER, "System Default"),
                (FileOpenTool.VSCODE, "VS Code"),
            ]
        ],
    )
    return frame


def create_text_with_button_frames_for_folders_opening(
    master: ctk.CTk | ctk.CTkFrame,
    text: Callable[[], str],
    path_generators: Callable[[str], list[Path]],
    types_of_folders: list[str],
) -> TextWithButtonsFrame:
    def open_or_create_and_open_folder_lambda(stringified_path: str):
        def inner():
            open_or_create_and_open_folder(
                Path(stringified_path),
                frame.update_buttons_text(
                    [
                        (
                            f"Open {type_of_folder}"
                            if check_folder_existence(path)
                            else f"Create {type_of_folder} and open"
                        )
                        for type_of_folder, path in zip(
                            types_of_folders,
                            path_generators(get_election_abbreviation()),
                        )
                    ]
                ),
            )

        return inner

    frame = TextWithButtonsFrame(
        master,
        text(),
        [
            (
                (
                    f"Open {type_of_folder}"
                    if check_folder_existence(path)
                    else f"Create {type_of_folder} and open"
                ),
                open_or_create_and_open_folder_lambda(str(path)),
            )
            for type_of_folder, path in zip(
                types_of_folders, path_generators(get_election_abbreviation())
            )
        ],
    )

    return frame


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.app_state = AppState.INITIAL
        self.elements = []

        self.title("Election Automation")
        self.geometry("1200x800")
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

        self.election_file = create_text_with_button_frames_for_file_opening(
            self,
            lambda: f"election-{get_election_abbreviation()}.json",
            elections_file_path,
            "election file",
            create_election_file_with_sensible_defaults,
        )

        self.election_file.grid(row=1, column=0, padx=20, pady=20)

        candidates_folder_name = lambda: f"{get_election_abbreviation()}-candidates"
        candidates_folder_exists = check_folder_existence(
            RO_DIRECTORY / "elections" / candidates_folder_name()
        )

        self.candidates_folder = create_text_with_button_frames_for_folders_opening(
            self,
            lambda: "Candidates folder",
            lambda abbr: [RO_DIRECTORY / "elections" / f"{abbr}-candidates"],
            ["Candidates folder"],
        )
        self.candidates_folder.grid(row=2, column=0, padx=20, pady=20)

        self.candidates_file = create_text_with_button_frames_for_file_opening(
            self,
            lambda: f"candidates-{get_election_abbreviation()}.json",
            candidates_file_path,
            "candidates info file",
            create_candidates_file_with_sensible_defaults,
        )
        self.candidates_file.grid(row=3, column=0, padx=20, pady=20)

        self.output_folders = create_text_with_button_frames_for_folders_opening(
            self,
            lambda: "Output folders",
            lambda abbr: [
                RO_DIRECTORY / "output" / abbr,
                RO_DIRECTORY / "latex-out" / abbr,
            ],
            ["Non-LaTeX output", "LaTeX output"],
        )
        self.output_folders.grid(row=4, column=0, padx=20, pady=20)

        self.data_filler_button = ctk.CTkButton(
            self, text="Run Data Filler", command=self.run_data_filler
        )
        self.data_filler_button.grid(row=5, column=0, padx=20, pady=20)

        self.elements: list[ctk.CTkBaseClass] = [
            self.election_abbreviation,
            self.election_file,
            self.candidates_folder,
            self.candidates_file,
            self.output_folders,
            self.data_filler_button,
        ]

    def update_state(self, intended_state: AppState) -> bool:
        transition = self.state_transitions.get((self.app_state, intended_state), None)
        if transition is None:
            return False
        else:
            transition()
            self.app_state = intended_state
            return True

    def run_data_filler(self):
        data_filler.setup()
        data_filler.main()

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
