import os
import sys
import traceback
import asyncio
from rich.prompt import Prompt
from geminicode.context import Context
from geminicode.gemini.config import GeminiConfig
from geminicode.gemini_mcp.client import MCPClientHandler
from geminicode.tools.tool_handler import ToolHandler
from geminicode.work_tree.tree import WorkTree
from geminicode.gemini.client import AIClient
from geminicode.console.console import ConsoleWrapper
from geminicode.utils.logger import logger
from geminicode.config import GEMINI_MODEL_2_0_FLASH, GEMINI_MODEL_2_5_FLASH_PREVIEW_05_20, MAX_MESSAGES_IN_CONTEXT


async def on_exit(ai_client: AIClient, console: ConsoleWrapper):
    console.print_exit()
    ai_client.delete_cache()
    await ai_client.cfg.mcp_handler.cleanup()

async def _run_cli_loop(ai_client: AIClient, console: ConsoleWrapper):
    """Runs the main CLI interaction loop."""
    while True:
        try:
            user_input = Prompt.ask("\n[user]You[/user]")

            if user_input.lower() in ["exit", "quit"]:
                await on_exit(ai_client, console)
                break

            if not user_input:
                continue

            ai_client.message_handler.add_text_message("user", user_input)
            await ai_client.process_messages()
            ai_client.reset_max_iterations()

            if len(ai_client.message_handler.messages) > MAX_MESSAGES_IN_CONTEXT:
                ai_client.summarize_previous_messages()
                # Save message history after summarization
            ai_client.message_handler.save_message_history()

            console.print_token_count(
                ai_client.message_handler.accumulated_token_count
            )

        except Exception as e:
            logger.error(f"An error occurred during CLI loop: {e}", exc_info=True)
            console.print_error(str(e), traceback.format_exc())
            continue

async def get_ai_client():
    ctx = Context(os.getcwd())
    mcp_client = MCPClientHandler()
    await mcp_client.initialize()
    
    ai_config = GeminiConfig(model=GEMINI_MODEL_2_5_FLASH_PREVIEW_05_20, work_tree=WorkTree(ctx), ctx=ctx, mcp_handler=mcp_client, tool_handler=ToolHandler())
    ai_client = AIClient(ai_config)
    return ai_client

async def main():
    console = ConsoleWrapper()
    ai_client = await get_ai_client()
    console.print_welcome()

    await _run_cli_loop(ai_client, console)


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
