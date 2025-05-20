from typing import Dict, Any, List
from geminicode.work_tree.tree import WorkTree
import subprocess

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
    """Handler for listing all files in the project database and cleaning up stale entries.
    
    Args:
        work_tree: The WorkTree instance containing the database connection
        params: Dictionary containing the parameters for the tool (empty in this case)
            
    Returns:
        str: A formatted string containing all file paths, or an error message
    """
    try:
        # Get all files from filesystem using find command
        result = subprocess.run(['find', work_tree.ctx.cwd], 
                              capture_output=True, text=True, check=True)
        fs_file_paths_set = set(result.stdout.strip().split('\n'))
        
        # Get all files from database
        cursor = work_tree.conn.cursor()
        cursor.execute("SELECT path FROM project_files")
        db_files = cursor.fetchall()
        
        db_file_paths_set = set()
        for file in db_files:
            db_file_paths_set.add(file[0])
        
        stale_files = []
        for file in db_file_paths_set:
            if file not in fs_file_paths_set:
                db_file_paths_set.remove(file)
                stale_files.append(file)

        # Remove stale files from database
        if stale_files:
            placeholders = ','.join('?' * len(stale_files))
            cursor.execute(f"DELETE FROM project_files WHERE path IN ({placeholders})", 
                         tuple(stale_files))
            work_tree.conn.commit()
        
        valid_files = list(db_file_paths_set)
        if not valid_files:
            return "No files found in the database"
            
        # Format the results as a numbered list
        return "\n".join(valid_files)
            
    except subprocess.CalledProcessError as e:
        return f"Error running the list_files tool: {str(e)}"