import google.genai as genai
from google.genai import types
import os
import datetime
from typing import Dict, Any, List, Callable
from geminicode.tools.create_file_tool import create_file_tool, create_file_tool_handler
from geminicode.tools.read_file_tool import read_file_tool, read_file_tool_handler
from geminicode.tools.write_file_tool import write_file_tool, write_file_tool_handler
from geminicode.tools.list_files_tool import list_files_tool, list_files_tool_handler
from geminicode.tools.run_cli_tool import run_cli_tool, run_cli_tool_handler
from geminicode.work_tree.tree import WorkTree
from geminicode.gemini.system_prompts import system_prompt


class AIClient:
    def __init__(self, work_tree: WorkTree):
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        self.last_time_cache_updated = None
        self.work_tree = work_tree
        
        self.model_name_for_generation = "gemini-2.0-flash"
        self.model_name_for_caching = f"models/{self.model_name_for_generation}"

        self.tools = [
            types.Tool(function_declarations=[
                read_file_tool(),
                write_file_tool(),
                list_files_tool(),
                create_file_tool(),
                run_cli_tool()
            ])
        ]
        
        self.tool_handlers: Dict[str, Callable] = {
            "read_file": read_file_tool_handler,
            "write_file": write_file_tool_handler,
            "list_files": list_files_tool_handler,
            "create_file": create_file_tool_handler,
            "run_cli": run_cli_tool_handler
        }
        
        self.messages = []

        # Common ToolConfig for reuse
        self.common_tool_config = types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode=types.FunctionCallingConfigMode.AUTO
            )
        )

        system_prompt_text = system_prompt
        project_index_text = self.work_tree.get_project_index_file_content()

        # Prepare content objects for API
        system_instruction_as_content = types.Content(parts=[types.Part(text=system_prompt_text)])
        project_index_as_content = types.Content(role="model", parts=[types.Part(text=project_index_text)])
        print(project_index_as_content)

        self.cached_content_obj = self.client.caches.create(
            model=self.model_name_for_caching,
            config=types.CreateCachedContentConfig(
                display_name='geminicode_cache',
                system_instruction=system_instruction_as_content,
                tools=self.tools,
                tool_config=self.common_tool_config,
                contents=[project_index_as_content],
                ttl='86400s'
            ),
        )
        
        # Config for generation when using cache: only temperature and cache name
        self.config = types.GenerateContentConfig(
            temperature=0.2,
            cached_content=self.cached_content_obj.name,
        )

        
    def add_text_message(self, message: str):
        self.messages.append(types.Content(
            role="user",
            parts=[types.Part(text=message)]
        ))

    def process_messages(self, max_iterations: int = 15) -> str:
        """Process a user query with tool support."""
        try:
            config_for_this_call = self.config

            if max_iterations == 0:
                config_for_this_call.tool_config.function_calling_config.mode = types.FunctionCallingConfigMode.NONE
                
            response = self.client.models.generate_content(
                model=self.model_name_for_generation,
                contents=self.messages,
                config=config_for_this_call # Use the appropriately configured object
            )
            
            print(f"Response: {response}")

            if response.candidates and \
               response.candidates[0].content and \
               response.candidates[0].content.parts and \
               response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call
                
                handler = self.tool_handlers.get(function_call.name)
                if handler:
                    result = handler(self.work_tree, dict(function_call.args))
                else:
                    return f"Unknown function call: {function_call.name}"

                function_response_part = types.Part.from_function_response(
                    name=function_call.name,
                    response={"result": result}
                )

                model_function_call_content = types.Content(
                    role="model",
                    parts=[types.Part(function_call=function_call)]
                )
                user_function_response_content = types.Content(
                    role="user",
                    parts=[function_response_part]
                )
                self.messages.append(model_function_call_content)
                self.messages.append(user_function_response_content)
                
                return self.process_messages(max_iterations - 1)

            text_response = response.text
            model_text_response_content = types.Content(
                role="model",
                parts=[types.Part(text=text_response)]
            )
            self.messages.append(model_text_response_content)
            return text_response

        except Exception as e:
            import traceback
            print(f"Error processing query: {str(e)}\nTraceback: {traceback.format_exc()}")
            return f"Error processing query: {str(e)}"
