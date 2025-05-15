import json
import google.genai as genai
from google.genai import types
import os
from geminicode.gemini.schemas import boolean_output_schema

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=["How does AI work?"],
    config=types.GenerateContentConfig(
        response_schema=boolean_output_schema,
        response_mime_type="application/json"
    )
)
data = json.loads(response.text)

result = data.get("result")
is_str = isinstance(result, str)
print(f"Is string: {is_str}")
print(f"Should continue: {data.get('result')}")