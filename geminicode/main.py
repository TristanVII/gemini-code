import os
import time
import sys
import traceback
import asyncio
from rich.prompt import Prompt
from geminicode.context import Context
from geminicode.gemini_mcp.client import MCPClientHandler
from geminicode.work_tree.tree import WorkTree
from geminicode.gemini.client import AIClient
from geminicode.console.console import ConsoleWrapper


async def main():
    console = ConsoleWrapper()
    try:
        ctx = Context(os.getcwd())
        # console.print(f"[info]Initialized in directory:[/info] {ctx.cwd}")
        tree = WorkTree(ctx)
        mcp_client = MCPClientHandler()
        await mcp_client.initialize()
        ai_client = AIClient(tree, ctx, console, mcp_client)
        console.print_welcome()

        while True:
            try:
                # Get user input with rich prompt
                user_input = Prompt.ask("\n[user]You[/user]")

                # Check for exit command
                if user_input.lower() in ["exit", "quit"]:
                    console.print_exit()
                    ai_client.delete_cache()
                    break

                # Skip empty input
                if not user_input:
                    continue

                # Process the query
                ai_client.message_handler.add_text_message("user", user_input)
                await ai_client.process_messages()
                ai_client.reset_max_iterations()

                # 1. Summarize previous messages. IF we have reached a count of > max iterations.
                # this is an arbitrary limit to prevent the AI from using too much context
                if len(ai_client.message_handler.messages) > ai_client.max_iterations:
                    ai_client.summarize_previous_messages()
                # 2. Create next step decision.

                # Display token count in a nice format
                console.print_token_count(
                    ai_client.message_handler.accumulated_token_count
                )

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


def run():
    """Synchronous wrapper for the async main function."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
