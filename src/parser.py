import json
import jsonschema
from argparse import ArgumentParser
from pathlib import Path
from importlib.resources import files
from .models import Prompt, FunctionRegistry
from .ui import print_error


def _get_args():
    """Parse and return command-line arguments.
    
    Returns:
        Dictionary containing parsed arguments (functions_definition, input, output, model, debug).
    """
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
    parser.add_argument(
        "--model",
        default="Qwen/Qwen3-0.6B",
        help="Identifier of the model on the HF Hub.",
        metavar="<model_identifier>"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    return parser.parse_args().__dict__


def _load_json(path: str):
    """Load and parse a JSON file.
    
    Args:
        path: Path to the JSON file.
        
    Returns:
        Parsed JSON data as a list.
        
    Raises:
        ValueError: If the JSON is invalid or malformed.
    """
    try:
        with open(path, "r") as f:
            return list(json.load(f))
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Error: Invalid json file: {path}:{e.lineno}:{e.colno} - {e.msg}"
        )


def _load_function_registry(path: str):
    """Load and validate a function registry from JSON file.
    
    Args:
        path: Path to the functions definition JSON file.
        
    Returns:
        FunctionRegistry object with validated function definitions.
        
    Raises:
        ValueError: If JSON is invalid or doesn't match schema.
    """
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
        raise ValueError(f"Error: Invalid config file: {path} - {e.message}")
    return FunctionRegistry(functions=json_file)


def _load_prompts(path: str):
    """Load and validate prompts from JSON file.
    
    Args:
        path: Path to the prompts JSON file.
        
    Returns:
        List of Prompt objects with validated data.
        
    Raises:
        ValueError: If JSON is invalid or doesn't match schema.
    """
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
        raise ValueError(f"Error: Invalid config file: {path} - {e.message}")
    return [Prompt(**p) for p in json_file]


def parse():
    """Parse configuration from arguments and load all required data.
    
    Loads function definitions, prompts, and model configuration from files
    and validates them. Handles all file I/O errors gracefully.
    
    Returns:
        Tuple of (function_registry, prompts, output_path, model_name, debug).
    """
    args = _get_args()
    try:
        function_registry = _load_function_registry(
            args["functions_definition"]
        )
        if not function_registry.names:
            raise ValueError(f"Invalid config file: '{args['input']}' - No functions provided")
        if any(not f.name for f in function_registry.functions):
            raise ValueError(f"Invalid config file: '{args['input']}' - Functions can't have empty names")
        if len(set(function_registry.names)) != len(function_registry.names):
            raise ValueError(f"Invalid config file: '{args['input']}' - Duplicated function names")
        prompts = _load_prompts(args["input"])
        if any(not p.prompt for p in prompts):
            raise ValueError(f"Invalid config file: '{args['input']}' - Prompt cant be an empty string")
        if not prompts:
            raise ValueError(f"Invalid config file: '{args['input']}' - No prompts provided")
        output_path = Path(args["output"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w") as f:
            ...
        model = args["model"]
        debug = args["debug"]
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
    return (function_registry, prompts, output_path, model, debug)
