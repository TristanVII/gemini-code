import google.genai as genai
from google.genai import types 
import os
from geminicode.gemini.messages.message_handler import MessageHandler
from geminicode.gemini.schemas import should_continue_schema
from geminicode.work_tree.tree import WorkTree
from geminicode.gemini.system_prompts import (
    system_prompt,
    should_continue_prompt,
    summarize_previous_messages_prompt,
)
import json
from geminicode.tools.tool_handler import ToolHandler
from geminicode.console.console import ConsoleWrapper
from geminicode.gemini_mcp.client import MCPClientHandler

class AIClient:
    def __init__(self, work_tree: WorkTree, ctx, console: ConsoleWrapper, mcp_client: MCPClientHandler):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.mcp_client = mcp_client
        self.tool_handler = ToolHandler()
        self.console = console
        self.last_time_cache_updated = None
        self.work_tree = work_tree
        self.message_handler = MessageHandler()
        self.max_iterations = 30
        self.ctx = ctx
        self.initialize()

    def get_tools_config(self, tool_choice: str):
        return types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode=tool_choice)
        )

    def reset_max_iterations(self):
        self.max_iterations = 30

    def generate_log_entry(self, timestamp: str, content: str) -> str:
        return f'<log date="{timestamp}">{content}</log>'

    async def process_messages(self) -> str:
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
                config=config_for_this_call,  # Use the appropriately configured object
            )
            
            token_count_cost = response.usage_metadata.total_token_count or 0
            self.message_handler.accumulated_token_count += token_count_cost

            if not response.candidates or not response.candidates[0].content.parts:
                issue = response.candidates[0].finish_reason
                self.message_handler.add_text_message(
                    "user",
                    f"Issue: {issue}"
                    + " If fails again with same issue back to back STOP tool calling for this run",
                )
                return await self.process_messages()

            return await self.handle_response(response)

        except Exception as e:
            import traceback

            self.console.print_error(
                e, "Error processing query", traceback.format_exc()
            )
            return f"Error processing query: {str(e)}"

    async def handle_response(self, response: types.GenerateContentResponse):
        for part in response.candidates[0].content.parts:
            if part.text:
                self.message_handler.add_text_message("model", part.text)
                self.console.print_gemini_message(part.text)
                if not part.function_call and self.max_iterations > 0 and self.should_continue_check():
                    return await self.process_messages()

            if part.function_call:
                function_call = part.function_call

                self.console.print_tool_call(function_call.name, function_call.args)
                handler = self.tool_handler.handlers.get(function_call.name)

                if handler:
                    try:
                        result = handler(self.work_tree, dict(**function_call.args))
                        self.console.print_tool_result(str(result) if result is not None else "")

                    except Exception as e:
                        error_msg = (
                            f"Error calling function {function_call.name}: {str(e)}"
                        )
                        self.console.print_tool_error(error_msg)
                        result = str(e)
                elif function_call.name in self.mcp_client.tool_name_to_session:
                    result = await self.mcp_client.call_tool(function_call.name, dict(**function_call.args))
                    self.console.print_tool_result(str(result) if result is not None else "")
                else:
                    self.console.print_unknown_function_call(function_call.name)
                    result = "Error: Unknown function call"

                self.message_handler.add_function_call_with_result(
                    function_call, result
                )

                return await self.process_messages()

    def should_continue_check(self):
        config = self.generation_config_no_tools
        config.response_schema = should_continue_schema
        config.response_mime_type = "application/json"
        messages = [self.message_handler.get_last_message()]
        messages.append(
            types.Content(
                role="user",
                parts=[
                    types.Part(text=should_continue_prompt(messages[0].parts[0].text))
                ],
            )
        )
        response = self.client.models.generate_content(
            model=self.model_name_for_generation, contents=messages, config=config
        )

        data = json.loads(response.text)
        result = data.get("should_continue", False)
        if result:
            self.message_handler.add_text_message("user", "Continue with next task")
        return result

    def delete_cache(self):
        for cache in self.client.caches.list():
            self.client.caches.delete(name=cache.name)

    def summarize_previous_messages(self):
        self.message_handler.add_text_message("user", summarize_previous_messages_prompt)
        response = self.client.models.generate_content(
            model=self.model_name_for_generation,
            # Added prompt to messages
            contents=self.message_handler.messages,
            config=self.generation_config_no_tools,
        )
        # Clear messages
        self.message_handler.messages = []
        self.message_handler.add_text_message("model", response.text)

    # Call this in main.py
    def initialize(self):
        self.model_name_for_generation = "gemini-2.5-flash-preview-05-20"
        self.model_name_for_caching = f"models/{self.model_name_for_generation}"

        self.tools = [types.Tool(function_declarations=self.tool_handler.tools)]
        system_instruction_as_content = types.Content(
            parts=[
                types.Part(text=system_prompt + "PROJECT FULL PATH: " + self.ctx.cwd)
            ]
        )

        self.delete_cache()

        # Tool config for when tools ARE enabled (usually AUTO)
        tool_config_for_cache = self.get_tools_config(
            types.FunctionCallingConfigMode.AUTO
        )

        self.cached_content_obj = self.client.caches.create(
            model=self.model_name_for_caching,
            config=types.CreateCachedContentConfig(
                display_name="geminicode_cache",
                system_instruction=system_instruction_as_content,
                tools=self.tools + self.mcp_client.tools,
                tool_config=tool_config_for_cache,
                ttl="86400s",
            ),
        )

        self.generation_config_with_cache = types.GenerateContentConfig(
            temperature=0.2,
            cached_content=self.cached_content_obj.name,
        )

        # Config for generation when tools should be explicitly disabled (and thus, cache isn't used for this call)
        self.generation_config_no_tools = types.GenerateContentConfig(
            temperature=0.2,
            tool_config=self.get_tools_config(types.FunctionCallingConfigMode.NONE),
            # No cached_content here, as we're overriding tool behavior.
        )

