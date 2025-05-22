from mcp import ClientSession, StdioServerParameters
from google.genai import _mcp_utils 
from mcp.client.stdio import stdio_client
from .github import GITHUB_SERVER_PARAMS
from typing import List, Dict
import asyncio
from contextlib import AsyncExitStack

class MCPClientHandler:
    def __init__(self):
        self.sessions: List[ClientSession] = []
        self.tools = []
        self.tool_name_to_session: Dict[str, ClientSession] = {}
        self._exit_stack = AsyncExitStack()
        self._session = None
        
    async def initialize(self):
        await self.create_github_session()

    # Ideally put this somewhere else
    # then initialize can just call all connection functions
    async def create_github_session(self):
        try:
            # Create stdio transport
            stdio_transport = await self._exit_stack.enter_async_context(
                stdio_client(GITHUB_SERVER_PARAMS)
            )
            read, write = stdio_transport
            
            # Create and initialize session
            session = await self._exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            
            # Get available tools
            tool_list = await session.list_tools()
            for tool in tool_list.tools:
                self.tool_name_to_session[tool.name] = session 
                self.tools.append(tool)
                
        except Exception as e:
            await self.cleanup()
            raise

    async def call_tool(self, name, args):
        session = self.tool_name_to_session[name]
        if not session:
            raise RuntimeError("MCP session not initialized")
        return await session.call_tool(name=name, arguments=args)

    def list_gemini_tools(self):
        return _mcp_utils.mcp_to_gemini_tools(self.tools)