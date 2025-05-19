import os
import time
import sys
import traceback
from rich.prompt import Prompt
from geminicode.context import Context
from geminicode.work_tree.tree import WorkTree
from geminicode.gemini.client import AIClient
from geminicode.console.console import ConsoleWrapper


def main():
    console = ConsoleWrapper()
    try:
        ctx = Context(os.getcwd())
        # console.print(f"[info]Initialized in directory:[/info] {ctx.cwd}")
        tree = WorkTree(ctx)
        ai_client = AIClient(tree, ctx, console)

        console.print_welcome()

        while True:
            try:
                # Get user input with rich prompt
                user_input = Prompt.ask("\n[user]You[/user]")

                # Check for exit command
                if user_input.lower() in ['exit', 'quit']:
                    console.print_exit()
                    ai_client.delete_cache()
                    break

                # Skip empty input
                if not user_input:
                    continue

                # Process the query
                ai_client.message_handler.add_text_message("user", user_input)
                ai_client.process_messages()
                ai_client.reset_max_iterations()

                # Display token count in a nice format
                console.print_token_count(
                    ai_client.message_handler.accumulated_token_count)


            except KeyboardInterrupt:
                console.print("\n[info]Exiting GeminiCode CLI.[/info]")
                ai_client.delete_cache()
                break
            except Exception as e:
                console.print_error(str(e), traceback.format_exc())
                continue

    except Exception as e:
        console.print_error(str(e), traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
