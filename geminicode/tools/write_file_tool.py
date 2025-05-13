from typing import Dict, Any
from geminicode.work_tree.tree import WorkTree
import os

def write_file_tool() -> Dict[str, Any]:
    """Tool definition for writing content to a file and updating the project database."""
    return {
        "name": "write_file",
        "description": "Write content to a file and update the project database",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The full path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file"
                }
            },
            "required": ["file_path", "content"]
        }
    }

def write_file_tool_handler(work_tree: WorkTree, params: Dict[str, Any]) -> str:
    """Handler for writing content to a file and updating the project database.
    
    Args:
        work_tree: The WorkTree instance containing the database connection
        params: Dictionary containing the parameters for the tool
            - file_path: The full path to the file to write
            - content: The content to write to the file
            
    Returns:
        str: Success message or error message
    """
    file_path = params.get("file_path")
    content = params.get("content")
    
    if not file_path or not content:
        return "Error: Both file_path and content parameters are required"

    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write to the actual file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Update the database
        cursor = work_tree.conn.cursor()
        cursor.execute("""
            INSERT INTO project_files (path, content, last_modified)
            VALUES (?, ?, strftime('%s', 'now'))
            ON CONFLICT(path) DO UPDATE SET
                content = excluded.content,
                last_modified = strftime('%s', 'now')
        """, (file_path, content))
        
        work_tree.conn.commit()
        return f"Successfully wrote content to {file_path}"
            
    except Exception as e:
        return f"Error writing file: {str(e)}"
