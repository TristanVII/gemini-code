import os
import sqlite3
import time
from geminicode.utils.files import get_git_ignore_file_content, read_file
DB_SCHEMA = """
    CREATE TABLE IF NOT EXISTS project_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT UNIQUE NOT NULL,
        last_modified REAL NOT NULL,
        content TEXT NOT NULL,
    );
    CREATE INDEX IF NOT EXISTS idx_path ON project_files (path);
    """
class WorkTree:
    def __init__(self, ctx):
        self.ctx = ctx
        self.seperator = "====="
        self.recently_changed_files = {}

        # all ran on init
        self.set_project_index_file_path()
        self.add_git_ignore_files()
        self.write_project_index()

    def set_project_index_file_path(self):
        base_dir = '/tmp'
        project_name = os.path.basename(self.ctx.cwd)
        self.project_index_path = os.path.join(base_dir, project_name)
        print('Project index file path:', self.project_index_path)

    def add_git_ignore_files(self):
        ignored_patterns = get_git_ignore_file_content(self.ctx.cwd)
        if ignored_patterns:
            self.ctx.ignored_files.extend(ignored_patterns)
    
    def _init_db(self):
        os.makedirs(self.project_index_path, exist_ok=True)
        self.conn = sqlite3.connect(self.project_index_path)
        cursor = self.conn.cursor()
        cursor.executescript(self.DB_SCHEMA)
        self.conn.commit()

    def walk_files(self, start_dir, ignored_files=[]):
        for dirpath, _, filenames in os.walk(start_dir):
            if any(ignored in dirpath for ignored in ignored_files if ignored):
                continue
            for filename in filenames:
                if any(ignored == filename for ignored in ignored_files if ignored):
                    continue
                if '.' not in filename:
                    continue
                yield os.path.join(dirpath, filename)
    
    def save_project_db(self):
        for file_path in self.walk_files(self.ctx.cwd, self.ctx.ignored_files):
            content = read_file(file_path).strip()
            if content:
                self.conn.execute("INSERT INTO project_files (path, content, last_modified) VALUES (?, ?, ?)", (file_path, content, time.time()))

    # TODO: ADD LOOP DB TO CREATE THE CACHED FILE
    def format_project_index_file(self, file_path, content):
        return f"{self.seperator}{file_path}{self.seperator}\n{content}{self.seperator}\nEND{self.seperator}\n"
