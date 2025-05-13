
import subprocess
from typing import Dict, Any
from geminicode.work_tree.tree import WorkTree

def run_cli_tool() -> Dict[str, Any]:
    """Tool definition for running a CLI command and capturing its output."""
    return {
        "name": "run_cli",
        "description": "Run a CLI command and return the output. IMPORTANT: Always ask permission before running a CLI command. Do not ask to run commands that have a long running time. If you are unsure, ask the user to confirm.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The CLI command to execute."
                }
            },
            "required": ["command"]
        }
    }

def run_cli_tool_handler(work_tree: WorkTree, params: Dict[str, Any]) -> str:
    """Handler for running a CLI command and capturing its output.
    
    Args:
        work_tree: The WorkTree instance (not directly used in this handler).
        params: Dictionary containing the parameters for the tool
            - command: The CLI command to execute
            
    Returns:
        str: The output of the CLI command, or an error message if the command fails
    """
    command = params.get("command")
    if not command:
        return "Error: Command parameter is required"

    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            return stdout
        else:
            return f"Error: Command failed with return code {process.returncode}\nStdout: {stdout}\nStderr: {stderr}"
            
    except Exception as e:
        return f"Error running command: {str(e)}"
