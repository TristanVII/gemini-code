from typing import Dict, Any, List
from geminicode.work_tree.tree import WorkTree

def list_files_tool() -> Dict[str, Any]:
    """Tool definition for listing all files in the project database."""
    return {
        "name": "list_files",
        "description": "List all files stored in the project database",
        "parameters": {
            "type": "object",
            "properties": {},  # No parameters needed
            "required": []
        }
    }

def list_files_tool_handler(work_tree: WorkTree, params: Dict[str, Any]) -> str:
    """Handler for listing all files in the project database.
    
    Args:
        work_tree: The WorkTree instance containing the database connection
        params: Dictionary containing the parameters for the tool (empty in this case)
            
    Returns:
        str: A formatted string containing all file paths, or an error message
    """
    try:
        cursor = work_tree.conn.cursor()
        cursor.execute("SELECT path FROM project_files ORDER BY path")
        results = cursor.fetchall()
        
        if not results:
            return "No files found in the database"
            
        # Format the results as a numbered list
        file_list = "\n".join(f"{i+1}. {path}" for i, (path,) in enumerate(results))
        return f"Files in database:\n{file_list}"
            
    except Exception as e:
        return f"Error listing files: {str(e)}"
