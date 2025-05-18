from geminicode.tools.expression_search_tool import expression_search_tool, expression_search_tool_handler
from geminicode.tools.create_file_tool import create_file_tool, create_file_tool_handler
from geminicode.tools.read_file_tool import read_file_tool, read_file_tool_handler
from geminicode.tools.write_file_tool import write_file_tool, write_file_tool_handler
from geminicode.tools.list_files_tool import list_files_tool, list_files_tool_handler
from geminicode.tools.run_cli_tool import run_cli_tool, run_cli_tool_handler


class ToolHandler:
    def __init__(self):
        self.handlers = {
            "expression_search": expression_search_tool_handler,
            "create_file": create_file_tool_handler,
            "read_file": read_file_tool_handler,
            "write_file": write_file_tool_handler,
            "list_files": list_files_tool_handler,
            "run_cli": run_cli_tool_handler
        }
        
        self.tools = [
            expression_search_tool(),
            create_file_tool(),
            read_file_tool(),
            write_file_tool(),
            list_files_tool(),
            run_cli_tool()
        ]