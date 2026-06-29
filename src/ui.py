"""Terminal UI components for displaying progress and results.

Provides rich console output for displaying function registries, prompts,
live function call generation, execution summaries, and error messages.
"""
from time import perf_counter, sleep
import json

from rich.console import Group, Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.rule import Rule
from rich.text import Text
from rich.live import Live
from rich.status import Status

from .models import FunctionRegistry, FunctionCall


def format_duration(seconds: float) -> str:
    """Format seconds into a human-readable duration string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted string (e.g., '1m 30s', '2h 15m 45s').
    """
    seconds = int(seconds)

    if seconds < 60:
        return f"{seconds}s"

    minutes, sec = divmod(seconds, 60)

    if minutes < 60:
        return f"{minutes}m {sec:02d}s"

    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m {sec:02d}s"


BORDER_COLOR = "bright_magenta"
TITLE_STYLE = "bold bright_white"
ACCENT = "bright_yellow"

console = Console()
print = console.print
status = Status("Generating...", console=console)


def log(message: str) -> None:
    """Log a debug message to the console.

    Args:
        message: Debug message to log.
    """
    console.log(message)


def no_log(message: str) -> None:
    """No-op log function for disabling debug output.

    Args:
        message: Message to ignore.
    """
    return


def print_title() -> None:
    """Print the application title banner."""
    title = Text(
        "\n☎  Call Me Maybe  ☎\n",
        justify="center",
        style=TITLE_STYLE,
    )

    print(
        Panel(
            title,
            border_style=BORDER_COLOR,
            padding=(1, 4),
            title=f"[{ACCENT}]By: smakkass[/]",
            title_align="left",
            subtitle="[dim]1337[/]",
            subtitle_align="right",
        )
    )


def print_function_registry(function_registry: FunctionRegistry) -> None:
    """Display the function registry as a formatted table.

    Args:
        function_registry: Registry containing function definitions to display.
    """
    table = Table(
        expand=True, row_styles=["", "dim"], header_style=f"{ACCENT} bold"
    )

    table.add_column("Function", style="bold green", ratio=2)
    table.add_column("Parameters", style="white dim", ratio=4)
    table.add_column("Returns", justify="center", style="yellow bold", ratio=1)

    for fn in function_registry.functions:
        params = ", ".join(fn.parameters.keys()) or "None"
        returns = fn.returns.type

        table.add_row(
            f"- {fn.name}",
            params,
            returns,
        )

    print(
        Panel(
            table,
            title="[bold]Function Registry[/]",
            border_style=BORDER_COLOR,
            padding=(0, 1),
        )
    )


def print_prompts(prompts: list[str]) -> None:
    """Display all prompts in a formatted panel.

    Args:
        prompts: List of prompt strings to display.
    """
    colors = [
        "bright_white",
        ACCENT,
    ]

    group = Group(
        *[
            Text(
                f"- {prompt}",
                style=colors[i % len(colors)],
            )
            for i, prompt in enumerate(prompts)
        ]
    )

    print(
        Panel(
            group,
            title="[bold]Prompts[/]",
            border_style=BORDER_COLOR,
        )
    )


def print_spacer(
    start_time: float | None = None, title: str | None = None
) -> None:
    """Print a visual separator line with optional elapsed time or title.

    Args:
        start_time: Optional start time to calculate and display elapsed duration.
        title: Optional title to display in the separator.
    """
    if start_time is None:
        rule = Rule(title, style=ACCENT)
    else:
        elapsed = perf_counter() - start_time
        rule = Rule(
            f"[bold cyan]{format_duration(elapsed)}[/]",
            align="right",
            style=ACCENT,
        )

    print()
    print(rule)
    print()


def print_function_call(
    i: int, n: int, prompt: str, function_call: FunctionCall
) -> Live:
    """Display a prompt and start live updating of the function call output.

    Args:
        i: Current prompt index (1-based).
        n: Total number of prompts.
        prompt: User prompt text to display.
        function_call: FunctionCall object to display and update.

    Returns:
        Tuple of (Live, Status) objects for updating the display.
    """
    panel = Panel(
        prompt,
        title=f"[{ACCENT}]Prompt {i}/{n}:[/]",
        title_align="left",
        border_style=BORDER_COLOR,
    )
    print(panel)
    syntax = Syntax(
        json.dumps(function_call.model_dump(), indent=4),
        "json",
        theme="monokai",
        line_numbers=True,
        indent_guides=True,
    )
    live = Live(
        Panel(
            syntax,
            border_style=BORDER_COLOR,
            title="Json:",
            title_align="left",
        ),
        console=console,
    )
    status.start()
    live.start()
    return live, status


def update_function_call(live: Live, function_call: FunctionCall) -> None:
    """Update the live display with the current function call state.

    Args:
        live: Live display object to update.
        function_call: Current FunctionCall object to display.
    """
    syntax = Syntax(
        json.dumps(function_call.model_dump(), indent=4),
        "json",
        theme="monokai",
        line_numbers=True,
        indent_guides=True,
    )
    panel = Panel(
        syntax, border_style=BORDER_COLOR, title="Json:", title_align="left"
    )
    live.update(panel)


def print_summary(start_time: float, n_functions: int, n_prompts: int) -> None:
    """Display execution summary with timing and statistics.

    Args:
        start_time: Start time for calculating total elapsed duration.
        n_functions: Number of available functions.
        n_prompts: Number of processed prompts.
    """
    table = Table(row_styles=["", "dim"], header_style=f"{ACCENT} bold")
    table.add_column("Metric")
    table.add_column("Value")

    elapsed = perf_counter() - start_time

    table.add_row("Elapsed", format_duration(elapsed), style="green bold")
    table.add_row("Functions", f"{n_functions}", style="green bold")
    table.add_row("Prompts", f"{n_prompts}", style="green bold")

    print(Panel.fit(table, title="Summary", border_style=BORDER_COLOR))


def print_error(message: str) -> None:
    """Display an error message and exit the application.

    Args:
        message: Error message to display.
    """
    panel = Panel(
        message,
        title="Error:",
        title_align="left",
        border_style="red",
    )
    print(panel)
    exit(1)


def print_exit() -> None:
    """Display keyboard interrupt message and cleanup."""
    status.stop()
    console.clear_live()
    console.clear()
    print()
    text = Text(
        "Keyboard interrupt detected.", style="bright_yellow", justify="center"
    )
    sub_text = Text("See you next time.", justify="center")
    pannel = Panel(
        Group(text, sub_text),
        padding=(2, 4),
        title="Interrupted",
        border_style="bright_red",
        title_align="left",
        subtitle="Ctrl + c",
        subtitle_align="right",
    )
    print(pannel)
