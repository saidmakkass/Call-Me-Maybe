from .models import FunctionDefinition, FunctionCall
from .llm import Model
from .ui import update_function_call
from typing import List
from rich.live import Live


def generate_function_name(
    model: Model,
    context: str,
    function_names: List[str],
    live: Live,
    function_call: FunctionCall,
) -> None:
    found_valid_name = False

    while True:
        logits = model.get_logits(model.encode(context + function_call.name))

        for token, _ in enumerate(logits):
            token_str = model.decode(token)
            if all(
                not s.startswith(function_call.name + token_str)
                for s in function_names
            ):
                if token_str == '"' and found_valid_name:
                    continue
                logits[token] = float("-inf")

        next_token = model.decode(model.next_token(logits))

        if next_token == '"' and found_valid_name:
            break

        function_call.name += next_token
        update_function_call(live, function_call)

        if function_call.name in function_names:
            found_valid_name = True


def generate_parameter_str(
    model: Model,
    context: str,
    live: Live,
    function_call: FunctionCall,
    param: str,
) -> None:
    function_call.parameters[param] = ""
    while True:
        logits = model.get_logits(
            model.encode(context + function_call.parameters[param])
        )
        next_token = model.decode(model.next_token(logits))
        if '"' in next_token:
            break
        function_call.parameters[param] += next_token
        update_function_call(live, function_call)


def is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def generate_parameter_float(
    model: Model,
    context: str,
    live: Live,
    function_call: FunctionCall,
    param: str,
) -> None:
    number = ""
    while True:
        logits = model.get_logits(model.encode(context + number))
        for token, _ in enumerate(logits):
            token_str = model.decode(token)
            if "," in token_str and token_str != ",":
                logits[token] = float("-inf")
            if token_str == "," and not is_float(number):
                logits[token] = float("-inf")
            if (
                token_str != ","
                and "." not in token_str
                and not is_float(number + token_str)
            ):
                logits[token] = float("-inf")
        next_token = model.decode(model.next_token(logits))
        if next_token == ",":
            break
        number += next_token
        function_call.parameters[param] = float(number)
        update_function_call(live, function_call)


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
    model: Model,
    context: str,
    function_definition: FunctionDefinition,
    live: Live,
    function_call: FunctionCall,
) -> None:
    for parameter, type in function_definition.parameters.items():
        context += f'"{parameter}": '
        match type.type:
            case "string":
                context += '"'
                function_call.parameters[parameter] = None
                update_function_call(live, function_call)
                generate_parameter_str(
                    model, context, live, function_call, parameter
                )
                context += f'{function_call.parameters[parameter]}",'
            case "number":
                function_call.parameters[parameter] = None
                update_function_call(live, function_call)
                generate_parameter_float(
                    model, context, live, function_call, parameter
                )
                context += f"{function_call.parameters[parameter]},"
            # case "integer":
            #     function_call.parameters[parameter] = generate_parameter_int()
            # case "boolean":
            #     function_call.parameters[parameter] = generate_parameter_bool()
