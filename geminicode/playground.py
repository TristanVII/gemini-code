import json
import google.genai as genai
from google.genai import types, _mcp_utils 

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import os
import asyncio

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
github_token = os.getenv("GITHUB_MCP")


server_params_docker = StdioServerParameters(
    command="docker",  # The executable to run
    args=[
        "run",
        "-i",
        "--rm",
        "-e",
        f"GITHUB_PERSONAL_ACCESS_TOKEN={github_token}",
        "ghcr.io/github/github-mcp-server",  # The Docker image
    ],
    env=None,  # Environment variables for the 'docker' command itself (usually not needed here)
)


def generate_response(mcp_tools):
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=["what tools do you have"],
        config=types.GenerateContentConfig(
            tools=_mcp_utils.mcp_to_gemini_tools(mcp_tools)
        )
    )
    return response


async def run():
    async with stdio_client(server_params_docker) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            list = await session.list_tools()
            response = generate_response(list.tools)

            print(response.candidates[0].content.parts[0].text)


if __name__ == "__main__":
    asyncio.run(run())
