import os
import sqlite3
import time
from geminicode.utils.files import get_git_ignore_file_content, read_file

# Corrected DB_SCHEMA (removed trailing comma)
DB_SCHEMA = """
    CREATE TABLE IF NOT EXISTS project_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT UNIQUE NOT NULL,
        last_modified REAL NOT NULL,
        content TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_path ON project_files (path);
"""


class WorkTree:
    def __init__(self, ctx):
        self.ctx = ctx
        # Assign class attribute to instance for clarity if needed or use WorkTree.DB_SCHEMA
        self.DB_SCHEMA = DB_SCHEMA

        # all ran on init
        self.set_project_index_file_path_name('project_index.db')
        self.add_git_ignore_files()
        self._init_db()
        self.save_project_db()

    def set_project_index_file_path_name(self, name):
        base_dir = '/tmp'
        project_name = os.path.basename(self.ctx.cwd)
        directory = os.path.join(base_dir, project_name)
        file_path = os.path.join(directory, name)
        return [directory, file_path]

    def add_git_ignore_files(self):
        if not hasattr(self.ctx, 'ignored_files') or not isinstance(self.ctx.ignored_files, list):
            self.ctx.ignored_files = []
        ignored_patterns = get_git_ignore_file_content(self.ctx.cwd)
        if ignored_patterns:
            self.ctx.ignored_files.extend(ignored_patterns)

    def _init_db(self):
        # Ensure the directory for the database file exists
        directory, file_path = self.set_project_index_file_path_name(
            'project_index.db')
        os.makedirs(directory, exist_ok=True)
        # Connect to the database FILE
        self.conn = sqlite3.connect(file_path)
        cursor = self.conn.cursor()
        cursor.executescript(self.DB_SCHEMA)  # or WorkTree.DB_SCHEMA
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

    def save_to_db(self, file_path, content):
        self.conn.execute("INSERT INTO project_files (path, content, last_modified) VALUES (?, ?, ?)",
                          (file_path, content, time.time()))
        self.conn.commit()

    def save_project_db(self):
        for file_path in self.walk_files(self.ctx.cwd, self.ctx.ignored_files):
            content = read_file(file_path)
            if content != None:
                try:
                    self.save_to_db(file_path, content)
                except sqlite3.IntegrityError:
                    print(f"Path {
                          file_path} already exists or another integrity error occurred. Updating instead.")
                    self.conn.execute("UPDATE project_files SET content = ?, last_modified = ? WHERE path = ?",
                                      (content, time.time(), file_path))
        self.conn.commit()  # Commit all changes after the loop
