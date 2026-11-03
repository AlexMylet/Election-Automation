
import os
from pathlib import Path

RO_DIRECTORY = Path(os.getcwd())
config_file_path = RO_DIRECTORY / "config.txt"

def get_election_abbreviation():
    # TODO - error handling here
    with open(config_file_path, "r") as config_file:
        for line in config_file.readlines():
            line = line.strip()
            if line.startswith("abbr"):
                # TODO - error handling here
                return line.split("=")[1]
    # TODO - error handling here
    raise NotImplementedError()


def write_election_abbreviation(abbr: str):
    # TODO - error handling here
    with open(config_file_path, "r") as config_file:
        lines = config_file.readlines()
        for index, line in enumerate(lines):
            if line.startswith("abbr"):
                lines[index] = f"abbr={abbr}\n"


    with open(config_file_path, "w") as config_file:
        config_file.writelines(lines)


ELECTION_FILE_EXTENSION = "json"
