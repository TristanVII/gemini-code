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
 ██║  ██║██╔════╝██║╚██╔╝██║██║██║╚██╗██║██║       ██║      ██║   ██║██║  ██║██╔════╝ 
 ╚██████╔╝███████╗██║ ╚═╝ ██║██║██║ ╚████║██║       ╚██████╗ ╚██████╔╝██████╔╝███████╗ 
  ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝        ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝ 
"""

class ConsoleWrapper(Console):
    def __init__(self):
        super().__init__()
        self.json_format = False
        
    def _get_json_output(self, data, type_name):
        if self.json_format:
            return json.dumps({
                "type": type_name,
                "data": data
            }, indent=2)
        return None
        
    def print_welcome(self):
        json_output = self._get_json_output({"message": "Welcome to GeminiCode CLI!"}, "welcome")
        if json_output:
            return json_output
        self.print(Panel(
            f"\n\n{GEMINI_CODE_ART}\n\nPress Ctrl+C to exit.\n\n",
            title="[bold cyan]Welcome to GeminiCode CLI![/bold cyan]",
            border_style="cyan",
            expand=False
        ))

    def print_error(self, e, title="Error", traceback_text=None):
        json_output = self._get_json_output({
            "title": title,
            "error": str(e),
            "traceback": traceback_text
        }, "error")
        if json_output:
            return json_output
        self.print(f"[red]{title}: {str(e)}[/red]")
        if traceback_text:
            self.print(Syntax(traceback_text, "python", theme="monokai"))

    def print_tool_error(self, error):
        json_output = self._get_json_output({"error": error}, "tool_error")
        if json_output:
            return json_output
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
        json_output = self._get_json_output({"message": text}, "gemini_message")
        if json_output:
            return json_output
        self.print(
            Panel(
                text,
                title="[bold magenta]Gemini[/bold magenta]",
                border_style="magenta",
                expand=False,
            )
        )

    def print_tool_result(self, result):
        json_output = self._get_json_output({"result": result}, "tool_result")
        if json_output:
            return json_output
        self.print(
            Panel(
                result,
                title="[bold green]Tool Result[/bold green]",
                border_style="green",
                expand=False,
            )
        )
        
    def print_unknown_function_call(self, name):
        json_output = self._get_json_output({"function": name}, "unknown_function")
        if json_output:
            return json_output
        self.print(
            Panel(
                f"Unknown function call: {name}",
                title="[bold yellow]Warning[/bold yellow]",
                border_style="yellow",
                expand=False))

    def print_tool_call(self, name, args):
        if not name:
            return
        json_output = self._get_json_output({
            "function": name,
            "arguments": args
        }, "tool_call")
        if json_output:
            return json_output
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
        json_output = self._get_json_output({"token_count": token_count}, "token_count")
        if json_output:
            return json_output
        self.print(f"[info]Token count:[/info] {token_count}")

    def print_exit(self):
        json_output = self._get_json_output({"message": "Exiting GeminiCode CLI!"}, "exit")
        if json_output:
            return json_output
        self.print(Panel(
            "Exiting GeminiCode CLI!",
            title="[bold cyan]Exiting GeminiCode CLI![/bold cyan]",
            border_style="cyan",
            expand=False
        ))
    