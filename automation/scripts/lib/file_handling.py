import json
from pathlib import Path
from typing import Any, Callable


def check_file_existence(file_path: Path) -> bool:
    try:
        fp = open(file_path)
    except OSError:
        return False
    else:
        fp.close()
        return True


def create_file(path: Path) -> None:
    with open(path, "x") as _:
        print(f"{path} created")


def create_file_and_write_json(path_builder: Callable[[str], Path]):
    def wrapper(f: Callable[[str], Any]):
        def inner(current_abbr: str):
            path = path_builder(current_abbr)
            create_file(path)
            data = f(current_abbr)
            with open(path, "w") as file:
                json.dump(data, file, indent=4)

        return inner

    return wrapper
