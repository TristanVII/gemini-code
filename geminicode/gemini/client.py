from google import genai
import os


class AIClient:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        self.last_time_cache_updated = None
        self.code_base_cache_name

    def generate_text(self, prompt):
        response = self.client.generate_content(prompt)
        return response.text
