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
    """Generate a valid function name token-by-token using the model.

    Uses constrained decoding to ensure valid function names are generated,
    by filtering logits to exclude tokens that don't make valid function names.

    Args:
        model: The language model instance.
        context: The context string to generate from.
        function_names: List of available function names for validation.
        live: Live display object for updating UI.
        function_call: FunctionCall object to update with generated name.
    """
    found_valid_name = False

    while True:
        logits = model.get_logits(model.encode(context + function_call.name))

        for token, _ in enumerate(logits):
            token_str = model.decode([token])
            if all(
                not s.startswith(function_call.name + token_str)
                for s in function_names
            ):
                if token_str == '"' and found_valid_name:
                    continue
                logits[token] = float("-inf")

        next_token = model.decode([model.next_token(logits)])

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
    """Generate a string parameter value token-by-token.

    Continues generating tokens until a closing quote is encountered,
    updating the function call and UI in real-time.

    Args:
        model: The language model instance.
        context: The context string to generate from.
        live: Live display object for updating UI.
        function_call: FunctionCall object to update with parameter value.
        param: The parameter name to generate for.
    """
    function_call.parameters[param] = ""
    while True:
        logits = model.get_logits(
            model.encode(context + function_call.parameters[param])
        )
        next_token = model.decode([model.next_token(logits)])
        if '"' in next_token:
            break
        function_call.parameters[param] += next_token
        update_function_call(live, function_call)
    function_call.parameters[param] = function_call.parameters[param].strip()
    update_function_call(live, function_call)


def is_float(s: str) -> bool:
    """Check if a string can be converted to a float.

    Args:
        s: String to validate.

    Returns:
        True if the string represents a valid float, False otherwise.
    """
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
    """Generate a float parameter value with constrained token decoding.

    Filters logits to ensure valid float syntax (digits, decimal point, signs)
    and stops at delimiters (comma or closing brace).

    Args:
        model: The language model instance.
        context: The context string to generate from.
        live: Live display object for updating UI.
        function_call: FunctionCall object to update with parameter value.
        param: The parameter name to generate for.
    """
    number = ""
    while True:
        logits = model.get_logits(model.encode(context + number))
        for token, _ in enumerate(logits):
            token_str = model.decode([token])
            if "," in token_str and token_str != ",":
                logits[token] = float("-inf")
            if "}" in token_str and token_str != "}":
                logits[token] = float("-inf")
            if (token_str == "," or token_str == "}") and not is_float(number):
                logits[token] = float("-inf")
            if (
                token_str != ","
                and token_str != "}"
                and "." not in token_str
                and not is_float(number + token_str)
            ):
                logits[token] = float("-inf")
        next_token = model.decode([model.next_token(logits)])
        if next_token == "," or next_token == "}":
            break
        number += next_token
        function_call.parameters[param] = float(number)
        update_function_call(live, function_call)


def generate_parameter_int(
    model: Model,
    context: str,
    live: Live,
    function_call: FunctionCall,
    param: str,
) -> None:
    """Generate an integer parameter value with constrained token decoding.

    Filters logits to ensure only digits are generated and stops at
    delimiters (comma or closing brace).

    Args:
        model: The language model instance.
        context: The context string to generate from.
        live: Live display object for updating UI.
        function_call: FunctionCall object to update with parameter value.
        param: The parameter name to generate for.
    """
    number = ""
    while True:
        logits = model.get_logits(model.encode(context + number))
        for token, _ in enumerate(logits):
            token_str = model.decode([token])
            if "," in token_str and token_str != ",":
                logits[token] = float("-inf")
            if "}" in token_str and token_str != "}":
                logits[token] = float("-inf")
            if (token_str == "," or token_str == "}") and not number.isdigit():
                logits[token] = float("-inf")
            if (
                token_str != ","
                and token_str != "}"
                and not (number + token_str).isdigit()
            ):
                logits[token] = float("-inf")
        next_token = model.decode([model.next_token(logits)])
        if next_token == "," or token_str == "}":
            break
        number += next_token
        function_call.parameters[param] = int(number)
        update_function_call(live, function_call)


def generate_parameter_bool(
    model: Model,
    context: str,
    live: Live,
    function_call: FunctionCall,
    param: str,
) -> None:
    """Generate a boolean parameter value with constrained token decoding.

    Filters logits to ensure only true or false are generated and stops once
    one of the two is generated.

    Args:
        model: The language model instance.
        context: The context string to generate from.
        live: Live display object for updating UI.
        function_call: FunctionCall object to update with parameter value.
        param: The parameter name to generate for.
    """
    output = ""
    result = bool()
    while True:
        logits = model.get_logits(model.encode(context + output))
        for token, _ in enumerate(logits):
            token_str = model.decode([token])
            if all(
                not s.startswith(output + token_str) for s in ("true", "false")
            ):
                logits[token] = float("-inf")
        next_token = model.decode([model.next_token(logits)])
        if "true" in (output + next_token).lower():
            result = True
            break
        if "false" in (output + next_token).lower():
            result = False
            break
    function_call.parameters[param] = result
    update_function_call(live, function_call)


def generate_function_parameters(
    model: Model,
    context: str,
    function_definition: FunctionDefinition,
    live: Live,
    function_call: FunctionCall,
) -> None:
    """Generate all parameters for a function based on its definition.

    Iterates through each parameter and calls the appropriate generator
    based on the parameter type (string, integer, float, or boolean).

    Args:
        model: The language model instance.
        context: The context string to generate from.
        function_definition: Definition of the function including parameters.
        live: Live display object for updating UI.
        function_call: FunctionCall object to populate with parameters.
    """
    for parameter, type in function_definition.parameters.items():
        context += f'"{parameter}": '
        function_call.parameters[parameter] = None
        update_function_call(live, function_call)
        match type.type:
            case "string":
                context += '"'
                generate_parameter_str(
                    model, context, live, function_call, parameter
                )
                context += f'{function_call.parameters[parameter]}",'
            case "number":
                generate_parameter_float(
                    model, context, live, function_call, parameter
                )
                context += f"{function_call.parameters[parameter]},"
            case "integer":
                generate_parameter_int(
                    model, context, live, function_call, parameter
                )
            case "boolean":
                generate_parameter_bool(
                    model, context, live, function_call, parameter
                )
