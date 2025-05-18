from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.json import JSON
import json

from rich.theme import Theme

# Create a custom theme
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "success": "green",
    "ai": "magenta",
    "user": "blue",
})
# --- ASCII Art Definition ---
GEMINI_CODE_ART = r"""
  ██████╗ ███████╗███╗   ███╗██╗███╗   ██╗██╗        ██████╗  ██████╗ ██████╗ ███████╗ 
 ██╔════╝ ██╔════╝████╗ ████║██║████╗  ██║██║       ██╔════╝ ██╔═══██╗██╔══██╗██╔════╝ 
 ██║ ███╗███████╗██╔████╔██║██║██╔██╗ ██║ ██║       ██║      ██║   ██║██║  ██║███████╗ 
 ██║  ██║██╔════╝██║╚██╔╝██║██║██║╚██╗██║ ██║       ██║      ██║   ██║██║  ██║██╔════╝ 
 ╚██████╔╝███████╗██║ ╚═╝ ██║██║██║ ╚████║██║       ╚██████╗ ╚██████╔╝██████╔╝███████╗ 
  ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝        ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝ 
"""

class ConsoleWrapper(Console):
    def __init__(self):
        super().__init__()
        
    def print_welcome(self):
        self.print(Panel(
            f"\n\n{GEMINI_CODE_ART}\n\nPress Ctrl+C to exit.\n\n",
            title="[bold cyan]Welcome to GeminiCode CLI![/bold cyan]",
            border_style="cyan",
            expand=False
        ))

    def print_error(self, e, title="Error", traceback_text=None):
        self.print(f"[red]{title}: {str(e)}[/red]")
        if traceback_text:
            self.print(Syntax(traceback_text, "python", theme="monokai"))


    def print_tool_error(self, error):
        self.print(
            Panel(
                error,
                title="[bold red]Tool Error[/bold red]",
                border_style="red",
                expand=False,
            )
        )

    def print_gemini_message(self, text):
        if not text:
            return
        self.print(
            Panel(
                text,
                title="[bold magenta]Gemini[/bold magenta]",
                border_style="magenta",
                expand=False,
            )
        )

    def print_tool_result(self, result):
        self.print(
            Panel(
                result,
                title="[bold green]Tool Result[/bold green]",
                border_style="green",
                expand=False,
            )
        )
        
    def print_unknown_function_call(self, name):
        self.print(
            Panel(
                f"Unknown function call: {name}",
                title="[bold yellow]Warning[/bold yellow]",
                border_style="yellow",
                expand=False))

    def print_tool_call(self, name, args):
        if not name or not args:
            return
        table = Table(
            title="[bold blue]Tool Call[/bold blue]", border_style="blue", expand=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Function", name)

        args_json = json.dumps(args, indent=2)
        table.add_row("Arguments", Syntax(
            args_json, "json", theme="monokai"))

        self.print(table)
    
    def print_token_count(self, token_count):
        self.print(f"[info]Token count:[/info] {token_count}")

    def print_exit(self):
        self.print(Panel(
            "Exiting GeminiCode CLI!",
            title="[bold cyan]Exiting GeminiCode CLI![/bold cyan]",
            border_style="cyan",
            expand=False
        ))
    