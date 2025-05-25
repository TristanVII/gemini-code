import google.genai as genai
from google.genai import types
import os
from geminicode.context import Context
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
from geminicode.gemini.config import GeminiConfig


class AIClient:
    def __init__(self, cfg: GeminiConfig):
        self.cfg = cfg
        self.client = genai.Client(api_key=cfg.API_KEY)
        self.console = ConsoleWrapper()
        self.last_time_cache_updated = None
        self.message_handler = cfg.message_handler
        self.max_iterations = cfg.max_ai_iterations
        self.initialize()

    def initialize(self):
        # Delete cache incase some were left over since you pay per hour.
        self.delete_cache()

        self.model_name_for_caching = f"models/{self.cfg.model}"

        self.tools = [types.Tool(function_declarations=self.cfg.tool_handler.tools)]

        system_instruction_as_content = types.Content(
            parts=[
                types.Part(
                    text=system_prompt + "PROJECT FULL PATH: " + self.cfg.ctx.cwd
                )
            ]
        )

        self.cached_content_obj = self.client.caches.create(
            model=self.model_name_for_caching,
            config=types.CreateCachedContentConfig(
                display_name="geminicode_cache",
                system_instruction=system_instruction_as_content,
                tools=self.tools + self.cfg.mcp_handler.tools,
                tool_config=self.cfg.get_tools_config(
                    types.FunctionCallingConfigMode.AUTO
                ),
                # TODO: MAKE CONFIGURABLE
                ttl="3600s",
            ),
        )
        # Cached config for ai. Includes Full system prompt, tools/MCP.
        self.generation_config_with_cache = types.GenerateContentConfig(
            temperature=self.cfg.temperature,
            cached_content=self.cached_content_obj.name,
            thinking_config=types.ThinkingConfig(
                thinking_budget=self.cfg.thinking_budget,
                include_thoughts=self.cfg.include_thoughts,
            )
        )

        self.generation_config_no_tools = types.GenerateContentConfig(
            temperature=self.cfg.temperature,
            tool_config=self.cfg.get_tools_config(types.FunctionCallingConfigMode.NONE),
        )

    def reset_max_iterations(self):
        self.max_iterations = self.cfg.max_ai_iterations

    def generate_content_failed_check(self, response: types.GenerateContentResponse):
        if (
            not response.candidates
            or not response.candidates[0].content
            or not response.candidates[0].content.parts
        ):
            finished_reason = "Generating content failed"
            if response.candidates[0].finish_reason:
                finished_reason = response.candidates[0].finish_reason

            self.message_handler.add_text_message("user", f"Issue: {finished_reason}")
            return True
        return False

    async def process_messages(self) -> str:
        self.max_iterations -= 1
        try:
            if self.max_iterations == 0:
                config_for_this_call = self.generation_config_no_tools
            else:
                config_for_this_call = self.generation_config_with_cache

            print("DEBUG: ", self.message_handler.messages)
            response = self.client.models.generate_content(
                model=self.cfg.model,
                contents=self.message_handler.messages,
                config=config_for_this_call,
            )

            token_count_cost = response.usage_metadata.total_token_count or 0
            self.message_handler.accumulated_token_count += token_count_cost

            if self.generate_content_failed_check(response):
                return await self.process_messages()

            return await self.handle_response(response)

        except Exception as e:
            import traceback

            self.console.print_error(
                e, "Error processing query", traceback.format_exc()
            )
            return f"Error processing query: {str(e)}"

    async def handle_response(self, response: types.GenerateContentResponse):
        thinking = False
        for part in response.candidates[0].content.parts:
            if part.thought:
                thinking = True
            else:
                thinking = False
                
            if part.function_call:
                await self.handle_part_function_call(part.function_call, thinking)

            if part.text:
                await self.handle_part_text(part.text, thinking)

            if part.function_call or (not thinking and self.max_iterations > 0 and self.should_continue_check()):
                return await self.process_messages()


    async def handle_part_function_call(self, function_call: types.FunctionCall, thinking: bool):
        self.console.print_tool_call(function_call.name, function_call.args)
        handler = self.cfg.tool_handler.handlers.get(function_call.name)

        if handler:
            try:
                result = handler(self.cfg.work_tree, dict(**function_call.args))
                self.console.print_tool_result(
                    str(result) if result is not None else ""
                , thinking)

            except Exception as e:
                error_msg = (
                    f"Error calling function {function_call.name}: {str(e)}"
                )
                self.console.print_tool_error(error_msg)
                result = str(e)
        elif function_call.name in self.cfg.mcp_handler.tool_name_to_session:
            result = await self.cfg.mcp_handler.call_tool(
                function_call.name, dict(**function_call.args)
            )
            self.console.print_tool_result(
                str(result) if result is not None else ""
            , thinking)
        else:
            self.console.print_unknown_function_call(function_call.name)
            result = "Error: Unknown function call"

        self.message_handler.add_function_call_with_result(
            function_call, result
        )

    async def handle_part_text(self, part: str, thinking: bool):
        if not thinking:
            self.message_handler.add_text_message("model", part)
        self.console.print_gemini_message(part, thinking)
    
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
            model=self.cfg.model, contents=messages, config=config
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
        self.message_handler.add_text_message(
            "user", summarize_previous_messages_prompt
        )
        response = self.client.models.generate_content(
            model=self.cfg.model,
            # Added prompt to messages
            contents=self.message_handler.messages,
            config=self.generation_config_no_tools,
        )
        # Clear messages
        self.message_handler.messages = []
        self.message_handler.add_text_message("model", response.text)
