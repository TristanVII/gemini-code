from google import genai
from google.genai import types
import os
from typing import Dict, Any, List, Callable
from geminicode.tools.create_file_tool import create_file_tool, create_file_tool_handler
from geminicode.tools.read_file_tool import read_file_tool, read_file_tool_handler
from geminicode.tools.write_file_tool import write_file_tool, write_file_tool_handler
from geminicode.tools.list_files_tool import list_files_tool, list_files_tool_handler
from geminicode.work_tree.tree import WorkTree
from geminicode.gemini.system_prompts import system_prompt


class AIClient:
    def __init__(self, work_tree: WorkTree):
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        self.last_time_cache_updated = None
        self.work_tree = work_tree
        self.messages = []
        
        # TODO: MAKE THESE CACHED
        # Add system prompt as the first message
        self.messages.append(types.Content(
            role="model",
            parts=[types.Part(text=system_prompt)]
        ))

        # add the project index file to the messages
        self.messages.append(types.Content(
            role="model",
            parts=[types.Part(text=self.work_tree.get_project_index_file_content())]
        ))
        
        # Define our tools
        self.tools = [
            types.Tool(function_declarations=[
                read_file_tool(),
                write_file_tool(),
                list_files_tool(),
                create_file_tool()
            ])
        ]
        
        # Map tool names to their handlers
        self.tool_handlers: Dict[str, Callable] = {
            "read_file": read_file_tool_handler,
            "write_file": write_file_tool_handler,
            "list_files": list_files_tool_handler,
            "create_file": create_file_tool_handler
        }
        
        # Configure the model with our tools
        self.config = types.GenerateContentConfig(
            temperature=0,  # Use 0 for more deterministic function calls
            tools=self.tools,
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="AUTO"  # Let the model decide when to use functions
                )
            )
        )

    def add_text_message(self, message: str):
        self.messages.append(types.Content(
            role="user",
            parts=[types.Part(text=message)]
        ))

    def process_messages(self) -> str:
        """Process a user query with tool support."""
        print(f"Processing messages: {self.messages}")
        try:
            # Get initial response from Gemini
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=self.messages,
                config=self.config
            )

            # Check for function calls in the response
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call
                
                # Get the appropriate handler from the map
                handler = self.tool_handlers.get(function_call.name)
                if handler:
                    result = handler(self.work_tree, dict(function_call.args))
                else:
                    return f"Unknown function call: {function_call.name}"

                # Create a function response part
                function_response_part = types.Part.from_function_response(
                    name=function_call.name,
                    response={"result": result}
                )

                # Append function call and result to contents
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
                
                return self.process_messages()

            text_response = response.text
            model_text_response_content = types.Content(
                role="model",
                parts=[types.Part(text=text_response)]
            )
            self.messages.append(model_text_response_content)
            # If no function call, return the direct response
            return text_response

        except Exception as e:
            return f"Error processing query: {str(e)}"
