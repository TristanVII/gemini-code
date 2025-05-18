from google.genai import types


class MessageHandler:
    def __init__(self):
        self.messages = []
        # set in process_messages
        self.accumulated_token_count = 0

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
    
    def get_last_message(self):
        return self.messages[-1]
        