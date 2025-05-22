from mcp import ClientSession, StdioServerParameters
from google.genai import _mcp_utils 
from mcp.client.stdio import stdio_client
from .github import GITHUB_SERVER_PARAMS
from typing import List, Dict

class MCPClientHandler:
    def __init__(self):
        self.sessions: List[ClientSession] = []
        self.tools = []
        self.tool_name_to_session: Dict[str, ClientSession] = {}
        
    async def initialize(self):
        await self.create_github_session()


    async def create_github_session(self):
        async with stdio_client(GITHUB_SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                self.sessions.append(session)
                tool_list = await session.list_tools()
                for tool in tool_list.tools:
                    self.tool_name_to_session[tool.name] = session
                    self.tools.append(tool)

    async def call_tool(self, name, args):
        session = self.tool_to_session[name]
        return await session.call_tool(name, args)


    def list_gemini_tools(self):
        return _mcp_utils.mcp_to_gemini_tools(self.tools)
