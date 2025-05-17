import os
import time
import sys
import traceback
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.theme import Theme
from geminicode.context import Context
from geminicode.work_tree.tree import WorkTree
from geminicode.gemini.client import AIClient

# Create a custom theme
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "success": "green",
    "ai": "magenta",
    "user": "blue",
})

console = Console(theme=custom_theme)

def print_welcome():
    welcome_text = """
    [bold cyan]Welcome to GeminiCode CLI![/bold cyan]
    [dim]Your AI-powered coding assistant[/dim]
    """
    console.print(Panel(welcome_text, border_style="cyan"))
    console.print("\n[dim]Type 'exit' to quit, or enter your query:[/dim]")

def print_error(error_msg, traceback_text=None):
    console.print(f"\n[error]Error:[/error] {error_msg}")
    if traceback_text:
        console.print(Syntax(traceback_text, "python", theme="monokai"))

def main():
    try:
        ctx = Context(os.getcwd())
        console.print(f"[info]Initialized in directory:[/info] {ctx.cwd}")
        tree = WorkTree(ctx)
        ai_client = AIClient(tree, ctx)

        print_welcome()
        
        while True:
            try:
                # Get user input with rich prompt
                user_input = Prompt.ask("\n[user]You[/user]")
                
                # Check for exit command
                if user_input.lower() in ['exit', 'quit']:
                    console.print("\n[info]Exiting GeminiCode CLI.[/info]")
                    break
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Process the query
                ai_client.message_handler.add_text_message("user", user_input)
                ai_client.process_messages()
                ai_client.reset_max_iterations()
                
                # Display token count in a nice format
                console.print(f"\n[info]Token count for query:[/info] {ai_client.message_handler.accumulated_token_count}")
                ai_client.message_handler.accumulated_token_count = 0

            except KeyboardInterrupt:
                console.print("\n[info]Exiting GeminiCode CLI.[/info]")
                break
            except Exception as e:
                print_error(str(e), traceback.format_exc())
                continue

    except Exception as e:
        print_error(str(e), traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 
