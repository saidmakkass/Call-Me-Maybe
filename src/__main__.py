from .parser import parse
from .llm import Model
from .models import FunctionCall, Output, FunctionRegistry, FunctionDefinition
from .generator import generate_function_name, generate_function_parameters
from .ui import print_title, print_function_registry, print_prompts, print_function_call, print_spacer, print_summary, update_function_call
from time import perf_counter
from rich.status import Status

def get_function(
    function_registry: FunctionRegistry, name: str
) -> FunctionDefinition:
    for f in function_registry.functions:
        if f.name == name:
            return f

def main():
    output = Output(output=[])
    function_registry, prompts, output_path = parse()
    function_names = function_registry.names
    model = Model()
    if not function_names:
        raise NotImplementedError("empty registry")
    function_registry_dump = function_registry.model_dump_json()
    print("\033[2J\033[H\033[3J", end="")
    print_title()
    print_spacer()
    print_function_registry(function_registry)
    print_spacer()
    print_prompts([p.prompt for p in prompts])
    print_spacer()
    start_time = perf_counter()
    status = Status("Generating...")
    status.start()
    for i, p in enumerate(prompts, start=1):
        prompt_start_time = perf_counter()
        function_call = FunctionCall(
            prompt=p.prompt, name="", parameters={}
        )
        live = print_function_call(i, len(prompts), p.prompt, function_call)
        context = (
            "You are a natural language to function call system.\n"
            "Given this function registry:\n"
            f"{function_registry_dump}\n"
            "Chose the appropriate function and its parameters based on the user input.\n"
            "{"
            f'"prompt": "{p.prompt}",'
            '"name": "'
        )
        generate_function_name(
            model, context, function_names, live, function_call
        )
        context += (
            f'{function_call.name}",' '"parameters": {'
        )
        generate_function_parameters(
            model, context, get_function(function_registry, function_call.name), live, function_call
        )
        output.add(function_call)
        with open(output_path, "w") as f:
            f.write(output.dump())
        live.stop()
        print_spacer(start_time=prompt_start_time)
    status.stop()

    print_summary(start_time, len(function_registry.functions), len(prompts))


if __name__ == "__main__":
    main()
