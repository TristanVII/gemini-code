import json
import os
from typing import Optional
from google.genai import types

class MessageHandler:
    def __init__(self, cwd: str):
        self.messages = []
        self.accumulated_token_count = 0
        self.history_file = f"/tmp/{cwd.split('/')[-1]}.json"
        self.load_message_history()

    def add_text_message(self, role: str, message: str):
        self.messages.append(types.Content(
            role=role,
            parts=[types.Part(text=message)]
        ))

    def add_function_call_with_result(self, function_call: types.FunctionCall, result: str):
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
    
    def get_last_message(self) -> Optional[types.Content]:
        if len(self.messages) == 0:
            return None
        return self.messages[-1]

    def save_message_history(self):
        try:
            # Convert types.Content objects to a serializable format
            serializable_messages = []
            for message in self.messages:
                serializable_parts = []
                for part in message.parts:
                    if part.text:
                        serializable_parts.append({"text": part.text})
                    elif part.function_call:
                        serializable_parts.append({
                            "function_call": {
                                "name": part.function_call.name,
                                "args": part.function_call.args
                            }
                        })
                    elif part.function_response:
                        serializable_parts.append({
                            "function_response": {
                                "name": part.function_response.name,
                                "response": part.function_response.response
                            }
                        })
                serializable_messages.append({"role": message.role, "parts": serializable_parts})

            with open(self.history_file, 'w') as f:
                json.dump(serializable_messages, f, indent=4)
        except Exception as e:
            print(f"Error saving message history: {e}")

    def load_message_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    loaded_messages = json.load(f)
                
                # Convert loaded data back to types.Content objects
                self.messages = []
                for msg_data in loaded_messages:
                    parts = []
                    for part_data in msg_data["parts"]:
                        if "text" in part_data:
                            parts.append(types.Part(text=part_data["text"]))
                        elif "function_call" in part_data:
                            parts.append(types.Part(function_call=types.FunctionCall(
                                name=part_data["function_call"]["name"],
                                args=part_data["function_call"]["args"]
                            )))
                        elif "function_response" in part_data:
                            parts.append(types.Part.from_function_response(
                                name=part_data["function_response"]["name"],
                                response=part_data["function_response"]["response"]
                            ))
                    self.messages.append(types.Content(role=msg_data["role"], parts=parts))
            except Exception as e:
                print(f"Error loading message history: {e}")
                self.messages = [] # Clear messages if loading fails
