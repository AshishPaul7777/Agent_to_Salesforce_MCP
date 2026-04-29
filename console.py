from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.text import Text

_theme = Theme({
    "step":    "bold cyan",
    "node":    "bold blue",
    "writer":  "bold yellow",
    "editor":  "bold magenta",
    "success": "bold green",
    "error":   "bold red",
    "dim":     "dim white",
    "result":  "white",
})

console = Console(theme=_theme)


def print_step(label: str, message: str) -> None:
    console.print(f"[step]  {label}[/step]  [dim]{message}[/dim]")


def print_node(name: str, message: str) -> None:
    console.print(f"\n[node][ {name} ][/node] {message}")


def print_writer(iteration: int, message: str) -> None:
    console.print(f"[writer]  Writer (iter {iteration})[/writer]  {message}")


def print_editor(score: int | None, approved: bool, message: str) -> None:
    tag = "[success]APPROVED[/success]" if approved else "[editor]REVISE[/editor]"
    score_str = f"score={score}" if score is not None else ""
    console.print(f"[editor]  Editor[/editor]  {tag} {score_str}  {message}")


def print_final(report: str) -> None:
    console.print(Panel(report, title="[success]Final Itinerary[/success]", border_style="green"))


def print_error(message: str) -> None:
    console.print(f"[error]ERROR[/error]  {message}")
