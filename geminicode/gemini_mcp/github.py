from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
import os

github_token = os.getenv("GITHUB_MCP")
GITHUB_SERVER_PARAMS = StdioServerParameters(
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
