import google.genai as genai
from google.genai import types
import os
import datetime
from typing import Dict, Any, List, Callable
from geminicode.gemini.messages.message_handler import MessageHandler
from geminicode.gemini.schemas import should_continue_schema
from geminicode.gemini.utils import debug_print_response
from geminicode.tools.expression_search_tool import expression_search_tool, expression_search_tool_handler
from geminicode.tools.create_file_tool import create_file_tool, create_file_tool_handler
from geminicode.tools.read_file_tool import read_file_tool, read_file_tool_handler
from geminicode.tools.write_file_tool import write_file_tool, write_file_tool_handler
from geminicode.tools.list_files_tool import list_files_tool, list_files_tool_handler
from geminicode.tools.run_cli_tool import run_cli_tool, run_cli_tool_handler
from geminicode.work_tree.tree import WorkTree
from geminicode.gemini.system_prompts import system_prompt, should_continue_prompt
import json


class AIClient:
    def __init__(self, work_tree: WorkTree):
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        self.last_time_cache_updated = None
        self.work_tree = work_tree
        self.message_handler = MessageHandler()
        self.max_iterations = 15


        self.model_name_for_generation = "gemini-2.0-flash"
        self.model_name_for_caching = f"models/{self.model_name_for_generation}"

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

        system_instruction_as_content = types.Content(parts=[types.Part(text=system_prompt_text)])

        for cache in self.client.caches.list():
            self.client.caches.delete(name=cache.name)

        # Tool config for when tools ARE enabled (usually AUTO)
        tool_config_for_cache = self.get_tools_config(types.FunctionCallingConfigMode.AUTO)

        self.cached_content_obj = self.client.caches.create(
            model=self.model_name_for_caching, # Ensure this is the specific model string like "models/gemini-2.0-flash"
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
            tool_config=self.get_tools_config(types.FunctionCallingConfigMode.NONE)
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
            
            print(f"Iterations left: {self.max_iterations}")
            response = self.client.models.generate_content(
                model=self.model_name_for_generation,
                contents=self.message_handler.messages,
                config=config_for_this_call # Use the appropriately configured object
            )
            
            token_count_cost = response.usage_metadata.total_token_count or 0
            self.message_handler.accumulated_token_count += token_count_cost
            
            if not response.candidates[0].content.parts:
                issue = response.candidates[0].finish_reason
                self.message_handler.add_text_message("user", f"Issue: {issue}" + " If fails again with same issue back to back STOP tool calling for this run")
                return self.process_messages()

            debug_print_response(response)

            return self.handle_response(response)

        except Exception as e:
            import traceback
            print(f"Error processing query: {str(e)}\nTraceback: {traceback.format_exc()}")
            return f"Error processing query: {str(e)}"

    
    def handle_response(self, response: types.GenerateContentResponse):
        for part in response.candidates[0].content.parts:
            if part.text:
                self.message_handler.add_text_message("model", part.text)
                
            if self.max_iterations == 0 or not self.should_continue_check():
                print(f'\n\nGemini: {part.text}')
            else:
                print(f'\n\nGemini: {part.text}')
                return self.process_messages()
            if part.function_call:
                function_call = part.function_call
                print(f"Function call: {function_call.name} with args: {json.dumps(function_call.args)}")

                handler = self.tool_handlers.get(function_call.name)
                if handler:
                    try:
                        result = handler(self.work_tree, dict(**function_call.args))
                    except Exception as e:
                        print(f"Error calling function {function_call.name}: {str(e)}")
                        result = str(e)
                else:
                    result = f"Unknown function call: {function_call.name}"

                self.message_handler.add_function_call_with_result(function_call, result)

                return self.process_messages()
    
    def should_continue_check(self):
        config = self.generation_config_no_tools
        config.response_schema = should_continue_schema
        config.response_mime_type = "application/json"
        messages = [self.message_handler.get_last_message()]
        messages.append(types.Content(
            role='user',
            parts=[types.Part(text=should_continue_prompt(messages[0].parts[0].text))]
        ))
        response = self.client.models.generate_content(
            model=self.model_name_for_generation,
            contents=messages,
            config=config
        )

        data = json.loads(response.text)
        result = data.get("should_continue", False)
        if result:
            self.message_handler.add_text_message("user", "Continue with next task")
        return result
        
    