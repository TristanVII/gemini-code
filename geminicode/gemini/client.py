import google.genai as genai
from google.genai import types
import os
import datetime
from typing import Dict, Any, List, Callable
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.json import JSON
from geminicode.gemini.messages.message_handler import MessageHandler
from geminicode.gemini.schemas import should_continue_schema
from geminicode.tools.expression_search_tool import expression_search_tool, expression_search_tool_handler
from geminicode.tools.create_file_tool import create_file_tool, create_file_tool_handler
from geminicode.tools.read_file_tool import read_file_tool, read_file_tool_handler
from geminicode.tools.write_file_tool import write_file_tool, write_file_tool_handler
from geminicode.tools.list_files_tool import list_files_tool, list_files_tool_handler
from geminicode.tools.run_cli_tool import run_cli_tool, run_cli_tool_handler
from geminicode.work_tree.tree import WorkTree
from geminicode.gemini.system_prompts import system_prompt, should_continue_prompt
import json

console = Console()

class AIClient:
    def __init__(self, work_tree: WorkTree, ctx):
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        self.last_time_cache_updated = None
        self.work_tree = work_tree
        self.message_handler = MessageHandler()
        self.max_iterations = 30
        self.ctx = ctx

        self.model_name_for_generation = "gemini-2.0-flash"
        self.model_name_for_caching = f"models/{
            self.model_name_for_generation}"

        self.tools = [
            types.Tool(function_declarations=[
                read_file_tool(),
                write_file_tool(),
                list_files_tool(),
                create_file_tool(),
                run_cli_tool(),
                expression_search_tool()
            ])
        ]

        self.tool_handlers: Dict[str, Callable] = {
            "read_file": read_file_tool_handler,
            "write_file": write_file_tool_handler,
            "list_files": list_files_tool_handler,
            "create_file": create_file_tool_handler,
            "run_cli": run_cli_tool_handler,
            "expression_search": expression_search_tool_handler
        }

        # Common ToolConfig for reuse
        system_prompt_text = system_prompt

        system_instruction_as_content = types.Content(
            parts=[types.Part(text=system_prompt_text + 'PROJECT FULL PATH: ' + self.ctx.cwd)])

        for cache in self.client.caches.list():
            self.client.caches.delete(name=cache.name)

        # Tool config for when tools ARE enabled (usually AUTO)
        tool_config_for_cache = self.get_tools_config(
            types.FunctionCallingConfigMode.AUTO)

        self.cached_content_obj = self.client.caches.create(
            # Ensure this is the specific model string like "models/gemini-2.0-flash"
            model=self.model_name_for_caching,
            config=types.CreateCachedContentConfig(
                display_name='geminicode_cache',
                system_instruction=system_instruction_as_content,
                tools=self.tools,  # Embed tools in the cache
                tool_config=tool_config_for_cache,  # Embed tool_config in the cache
                ttl='86400s'
            ),
        )

        # Config for generation when using cache (tools are enabled via the cache's config)
        self.generation_config_with_cache = types.GenerateContentConfig(
            temperature=0.2,
            cached_content=self.cached_content_obj.name
            # DO NOT set tools or tool_config here again, as they are in the cache.
        )

        # Config for generation when tools should be explicitly disabled (and thus, cache isn't used for this call)
        self.generation_config_no_tools = types.GenerateContentConfig(
            temperature=0.2,
            tool_config=self.get_tools_config(
                types.FunctionCallingConfigMode.NONE)
            # No cached_content here, as we're overriding tool behavior.
        )

    def get_tools_config(self, tool_choice: str):
        return types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode=tool_choice
            )
        )

    def reset_max_iterations(self):
        self.max_iterations = 15

    def generate_log_entry(self, timestamp: str, content: str) -> str:
        return f'<log date="{timestamp}">{content}</log>'

    def process_messages(self) -> str:
        """Process a user query with tool support."""
        self.max_iterations -= 1
        try:
            # Select the appropriate generation configuration
            if self.max_iterations == 0:
                # When max_iterations is 0, use the config that explicitly disables tools
                # and does NOT use the cache (since the cache has tools enabled).
                config_for_this_call = self.generation_config_no_tools
            else:
                # Otherwise, use the config that leverages the cache (which has tools enabled).
                config_for_this_call = self.generation_config_with_cache

            # print(f"Iterations left: {self.max_iterations}")
            response = self.client.models.generate_content(
                model=self.model_name_for_generation,
                contents=self.message_handler.messages,
                config=config_for_this_call  # Use the appropriately configured object
            )

            token_count_cost = response.usage_metadata.total_token_count or 0
            self.message_handler.accumulated_token_count += token_count_cost

            if not response.candidates[0].content.parts:
                issue = response.candidates[0].finish_reason
                self.message_handler.add_text_message("user", f"Issue: {
                                                      issue}" + " If fails again with same issue back to back STOP tool calling for this run")
                return self.process_messages()

            return self.handle_response(response)

        except Exception as e:
            import traceback
            print(f"Error processing query: {
                  str(e)}\nTraceback: {traceback.format_exc()}")
            return f"Error processing query: {str(e)}"

    def handle_response(self, response: types.GenerateContentResponse):
        for part in response.candidates[0].content.parts:
            if part.text:
                self.message_handler.add_text_message("model", part.text)

            if self.max_iterations == 0 or not self.should_continue_check():
                # Format AI response in a panel with safe text handling
                try:
                    text_content = str(part.text) if part.text else ""
                    console.print(Panel(
                        text_content,
                        title="[bold magenta]Gemini[/bold magenta]",
                        border_style="magenta",
                        expand=False
                    ))
                except Exception as e:
                    console.print(f"[red]Error displaying response: {str(e)}[/red]")
            else:
                # Format AI response in a panel with safe text handling
                try:
                    text_content = str(part.text) if part.text else ""
                    # sometimes message is none so dont show that
                    if text_content != "":
                        console.print(Panel(
                            text_content,
                            title="[bold magenta]Gemini[/bold magenta]",
                            border_style="magenta",
                            expand=False
                        ))
                except Exception as e:
                    console.print(f"[red]Error displaying response: {str(e)}[/red]")
                return self.process_messages()

            if part.function_call:
                function_call = part.function_call
                
                try:
                    # Create a table for function call details
                    table = Table(title="[bold blue]Tool Call[/bold blue]", border_style="blue", expand=False)
                    table.add_column("Property", style="cyan")
                    table.add_column("Value", style="green")
                    
                    # Add function name
                    table.add_row("Function", function_call.name)
                    
                    # Add arguments in a formatted way
                    args_json = json.dumps(function_call.args, indent=2)
                    table.add_row("Arguments", Syntax(args_json, "json", theme="monokai"))
                    
                    console.print(table)
                except Exception as e:
                    console.print(f"[red]Error displaying tool call: {str(e)}[/red]")

                handler = self.tool_handlers.get(function_call.name)
                if handler:
                    try:
                        result = handler(self.work_tree, dict(**function_call.args))
                        
                        # Format the result in a panel with safe text handling
                        try:
                            result_text = str(result) if result is not None else ""
                            console.print(Panel(
                                result_text,
                                title=f"[bold green]Tool Result: {function_call.name}[/bold green]",
                                border_style="green",
                                expand=False
                            ))
                        except Exception as e:
                            console.print(f"[red]Error displaying result: {str(e)}[/red]")
                        
                    except Exception as e:
                        error_msg = f"Error calling function {function_call.name}: {str(e)}"
                        console.print(Panel(
                            error_msg,
                            title="[bold red]Tool Error[/bold red]",
                            border_style="red",
                            expand=False
                        ))
                        result = str(e)
                else:
                    result = f"Unknown function call: {function_call.name}"
                    console.print(Panel(
                        result,
                        title="[bold yellow]Warning[/bold yellow]",
                        border_style="yellow",
                        expand=False
                    ))

                self.message_handler.add_function_call_with_result(
                    function_call, result)

                return self.process_messages()

    def should_continue_check(self):
        config = self.generation_config_no_tools
        config.response_schema = should_continue_schema
        config.response_mime_type = "application/json"
        messages = [self.message_handler.get_last_message()]
        messages.append(types.Content(
            role='user',
            parts=[types.Part(text=should_continue_prompt(
                messages[0].parts[0].text))]
        ))
        response = self.client.models.generate_content(
            model=self.model_name_for_generation,
            contents=messages,
            config=config
        )

        data = json.loads(response.text)
        result = data.get("should_continue", False)
        if result:
            self.message_handler.add_text_message(
                "user", "Continue with next task")
        return result
