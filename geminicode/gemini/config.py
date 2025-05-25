# File that holds the config parameters for the gemini client

import os
from google.genai import types 
from geminicode.context import Context
from geminicode.gemini.messages.message_handler import MessageHandler
from geminicode.gemini_mcp.client import MCPClientHandler
from geminicode.tools.tool_handler import ToolHandler
from geminicode.work_tree.tree import WorkTree


class GeminiConfig:
    def __init__(self, model: str, work_tree: WorkTree, ctx: Context, mcp_handler: MCPClientHandler, tool_handler: ToolHandler):
        self.API_KEY = os.getenv("GEMINI_API_KEY")
        self.model = model
        self.work_tree = work_tree
        self.ctx = ctx
        self.mcp_handler = mcp_handler
        self.tool_handler = tool_handler
        self.message_handler = MessageHandler(ctx.cwd)
        
        
        # Configurable params
        self.max_ai_iterations = 30
        self.thinking_budget = 4096 # 0 for disabled
        self.temperature = 0.2
        self.include_thoughts = True

    def get_tools_config(self, mode: types.FunctionCallingConfigMode):
        return types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode=mode)
        )