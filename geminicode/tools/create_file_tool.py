from typing import Dict, Any
from geminicode.work_tree.tree import WorkTree
from geminicode.utils.files import create_file

def create_file_tool() -> Dict[str, Any]:
    """Tool definition for creating a new file in the project.
    
    This tool should be used before write_file_tool when a file doesn't exist.
    It creates an empty file at the specified path, ensuring the file exists
    before any write operations are attempted.
    """
    return {
        "name": "create_file",
        "description": "Creates a new empty file at the specified path. Use this tool before write_file_tool when the target file doesn't exist.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path where the new file should be created, relative to the project root"
                }
            },
            "required": ["path"]
        }
    }

def create_file_tool_handler(work_tree: WorkTree, params: Dict[str, Any]) -> str:
    """Handler for creating a new file.
    
    Args:
        work_tree: The WorkTree instance containing the database connection
        params: Dictionary containing the parameters for the tool
            - path: The path where the new file should be created
            
    Returns:
        str: A success message with the file path, or an error message
    """
    try:
        file_path = params.get("path")
        if not file_path:
            return "Error: No file path provided"
            
        # Create the file
        success = create_file(file_path)
        
        if success:
            work_tree.conn.execute(
                "INSERT INTO project_files (path, content, last_modified) VALUES (?, ?, ?)",
                (file_path, "", work_tree.last_time_cache_updated)
            )
            work_tree.conn.commit()
            return f"Successfully created file: {file_path}"
        else:
            return f"Failed to create file: {file_path}"
            
    except FileExistsError:
        return f"File already exists: {file_path}"
    except Exception as e:
        return f"Error creating file: {str(e)}"
