from typing import Dict, Any
from geminicode.work_tree.tree import WorkTree

def read_file_tool() -> Dict[str, Any]:
    """Tool definition for reading file content from the project database."""
    return {
        "name": "read_file",
        "description": "Read the content of a file from the project database",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The full path to the file to read"
                }
            },
            "required": ["file_path"]
        }
    }

def read_file_tool_handler(work_tree: WorkTree, params: Dict[str, Any]) -> str:
    """Handler for reading file content from the project database.
    
    Args:
        work_tree: The WorkTree instance containing the database connection
        params: Dictionary containing the parameters for the tool
            - file_path: The full path to the file to read
            
    Returns:
        str: The content of the file if found, or an error message if not found
    """
    file_path = params.get("file_path")
    if not file_path:
        return "Error: file_path parameter is required"

    try:
        cursor = work_tree.conn.cursor()
        cursor.execute("SELECT content FROM project_files WHERE path = ?", (file_path,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        else:
            return f"Error: File not found in database: {file_path}"
            
    except Exception as e:
        return f"Error reading file from database: {str(e)}"
