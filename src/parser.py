import json
import jsonschema
from argparse import ArgumentParser
from pathlib import Path
from importlib.resources import files
from .models import Prompt, FunctionRegistry
from .ui import print_error


def _get_args():
    parser = ArgumentParser(
        prog="uv run python -m src",
        description="Transform Natural Language to Function Calls",
        epilog="This project has been created as part of the 42 curriculum by "
        "smakkass",
    )
    parser.add_argument(
        "--functions_definition",
        default="data/input/functions_definition.json",
        help="Path to functions definition file",
        metavar="<function_definition_file>",
    )
    parser.add_argument(
        "--input",
        default="data/input/function_calling_tests.json",
        help="Path to input file",
        metavar="<input_file>",
    )
    parser.add_argument(
        "--output",
        default="data/output/function_calls.json",
        help="Path to output file",
        metavar="<output_file>",
    )
    return parser.parse_args().__dict__


def _load_json(path: str):
    try:
        with open(path, "r") as f:
            return list(json.load(f))
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Error: Invalid json file: {path}:{e.lineno}:{e.colno} - {e.msg}"
        )


def _load_function_registry(path: str):
    json_file = _load_json(path)
    schema_dir = files(__package__) / "schemas"
    with open(schema_dir.joinpath("functions_definition_schema.json")) as f:
        schema = json.load(f)
    try:
        jsonschema.validate(
            instance=json_file,
            schema=schema,
        )
    except jsonschema.ValidationError as e:
        raise ValueError(f"Error: Invalid config file: {path}")
    return FunctionRegistry(functions=json_file)


def _load_prompts(path: str):
    json_file = _load_json(path)
    schema_dir = files(__package__) / "schemas"
    with open(schema_dir.joinpath("input_schema.json")) as f:
        schema = json.load(f)
    try:
        jsonschema.validate(
            instance=json_file,
            schema=schema,
        )
    except jsonschema.ValidationError as e:
        raise ValueError(f"Error: Invalid config file: {path} ({e.message})")
    return [Prompt(**p) for p in json_file]


def parse():
    args = _get_args()
    try:
        function_registry = _load_function_registry(
            args["functions_definition"]
        )
        prompts = _load_prompts(args["input"])
        output_path = Path(args["output"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w") as f:
            ...
    except FileNotFoundError as e:
        print_error(f"Missing input file: '{e.filename}'")
    except NotADirectoryError as e:
        print_error(f"Not a directory: '{e.filename}'")
    except IsADirectoryError as e:
        print_error(f"Is a directory: '{e.filename}'")
    except PermissionError as e:
        print_error(f"Insufficient permissions: '{e.filename}'")
    except FileExistsError as e:
        print_error(f"File exists: '{e.filename}'")
    except OSError as e:
        print_error(f"{e}")
    except ValueError as e:
        print_error(f"{e}")
    return (function_registry, prompts, output_path)
