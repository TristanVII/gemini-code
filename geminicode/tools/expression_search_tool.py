import subprocess
from typing import Dict, Any, List
from geminicode.work_tree.tree import WorkTree # Assuming WorkTree might be needed later or for consistency

def expression_search_tool() -> Dict[str, Any]:
    """Tool definition for searching for an expression in files and returning file paths."""
    return {
        "name": "expression_search",
        "description": "Search for an expression (literal string or regex) in files using ripgrep (rg) and return a list of matching file paths. It runs `rg -l 'search_expression'`. For literal searches (is_regex=False, default), the tool uses ripgrep's fixed string option (`-F`), so you do not need to escape regex characters in the 'expression' string itself. Ensure the expression argument is correctly passed. When using the output files, please make sure to use their FULL PATH.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The expression (string or regex) to search for."
                },
                "is_regex": {
                    "type": "boolean",
                    "description": "Whether the expression is a regex. Defaults to false (literal string search)."
                }
            },
            "required": ["expression"]
        }
    }

def expression_search_tool_handler(work_tree: WorkTree, params: Dict[str, Any]) -> str:
    """Handler for searching for an expression in files.
    
    Args:
        work_tree: The WorkTree instance (used to get the cwd for the search).
        params: Dictionary containing the parameters for the tool
            - expression: The string or regex to search for.
            - is_regex: Boolean indicating if the expression is a regex (default: False).
            
    Returns:
        str: A string containing a list of matching file paths (one per line), 
             or an error message if the command fails or no expression is provided.
    """
    expression = params.get("expression")
    if not expression:
        return "Error: Expression parameter is required"

    is_regex = params.get("is_regex", False) # Default to False if not provided
    
    # Determine the directory to search in
    search_dir = None
    if work_tree and hasattr(work_tree, 'ctx') and hasattr(work_tree.ctx, 'cwd'):
        search_dir = work_tree.ctx.cwd

    try:
        command_parts = ['rg', '--color=never', '--files-with-matches'] # Use --files-with-matches which is equivalent to -l
        if not is_regex:
            command_parts.append('--fixed-strings') # -F, --fixed-strings: Treat the pattern as a literal string
        
        command_parts.append(expression)
        
        # Explicitly add the directory to search if available
        if search_dir:
             command_parts.append(search_dir)
        else:
            # If no directory context, inform the user or rely on rg's default behavior (current dir)
             print("Warning: No search directory context provided via WorkTree. Searching from current working directory.")


        # Using shell=False is generally safer, passing args as a list
        process = subprocess.Popen(command_parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=search_dir) # Pass explicit cwd if available
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            if stdout:
                return stdout # Returns a string, with each file path on a new line
            else:
                # rg returns 0 even if no matches, but stdout will be empty
                return "No files found matching the expression."
        elif process.returncode == 1: # rg returns 1 if no matches are found
             return "No files found matching the expression."
        else:
             # rg returns 2 for actual errors (e.g., directory not found)
             # Include stderr for better diagnostics
             error_message = f"Error: Command failed with return code {process.returncode}"
             if stderr:
                 error_message += f"\nStderr: {stderr.strip()}"
             if stdout: # Sometimes rg might print partial info to stdout even on error
                 error_message += f"\nStdout: {stdout.strip()}"
             return error_message
            
    except FileNotFoundError:
        return "Error: ripgrep (rg) command not found. Please ensure it is installed and in your PATH."
    except Exception as e:
        return f"Error running command: {str(e)}"

