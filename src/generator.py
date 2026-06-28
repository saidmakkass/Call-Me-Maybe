from .models import FunctionDefinition
from .llm import Model
from typing import List, Dict, Union


def generate_function_name(
    model: Model, context: str, function_names: List[str]
) -> str:
    chosen_name = ""
    found_valid_name = False

    while True:
        logits = model.get_logits(model.encode(context + chosen_name))

        for token, _ in enumerate(logits):
            token_str = model.decode(token)

            if all(
                not s.startswith(chosen_name + token_str)
                for s in function_names
            ):
                if token_str == '"' and found_valid_name:
                    continue
                logits[token] = float("-inf")

        next_token = model.decode(model.next_token(logits))

        if next_token == '"' and found_valid_name:
            break

        chosen_name += next_token

        if chosen_name in function_names:
            found_valid_name = True

    return chosen_name


def generate_parameter_str(model: Model, context: str) -> str:
    string = ""
    while True:
        logits = model.get_logits(model.encode(context + string))
        next_token = model.decode(model.next_token(logits))
        if '"' in next_token:
            break
        string += next_token
    return string


def is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def generate_parameter_float(model: Model, context: str) -> float:
    number = ""
    while True:
        logits = model.get_logits(model.encode(context + number))
        for token, _ in enumerate(logits):
            token_str = model.decode(token)
            # if token_str.startswith("-") and len(number) > 0:
            #     logits[token] = float("-inf")
            if token_str == "," and not is_float(number):
                logits[token] = float("-inf")
            if (
                not token_str.isdigit()
                and not "." in token_str
                and not "," in token_str
                and not "-" in token_str
            ):
                logits[token] = float("-inf")
        next_token = model.decode(model.next_token(logits))
        if "," in next_token:
            break
        number += next_token
        return float(number)


def generate_parameter_int(model: Model, context: str) -> int:
    number = ""
    while True:
        logits = model.get_logits(model.encode(context + number))
        for token, _ in enumerate(logits):
            token_str = model.decode(token)
            if not token_str.isdigit() and not (
                token_str == "," and len(number)
            ):
                logits[token] = float("-inf")
        next_token = model.decode(model.next_token(logits))
        if token_str == ",":
            break
        number += next_token
    return int(number)


def generate_function_parameters(
    model: Model, context: str, function_definition: FunctionDefinition
) -> Dict[str, Union[str, int, float, bool]]:
    output = dict()
    for parameter, type in function_definition.parameters.items():
        context += f'"{parameter}": '
        match type.type:
            case "string":
                context += '"'
                output[parameter] = generate_parameter_str(model, context)
                context += f'{output[parameter]}",'
            case "number":
                output[parameter] = generate_parameter_float(model, context)
                context += f"{output[parameter]},"
            # case "integer":
            #     output[parameter] = generate_parameter_int()
            # case "boolean":
            #     output[parameter] = generate_parameter_bool()
    return output
