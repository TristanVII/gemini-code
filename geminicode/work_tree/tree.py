import os

from geminicode.utils.files import get_git_ignore_file_content, read_file
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
        self.project_index_file_path = os.path.join(base_dir, project_name, 'project_index.txt')
        print('Project index file path:', self.project_index_file_path)

    def add_git_ignore_files(self):
        ignored_patterns = get_git_ignore_file_content(self.ctx.cwd)
        if ignored_patterns:
            self.ctx.ignored_files.extend(ignored_patterns)

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
    
    def write_project_index(self):
        index_dir = os.path.dirname(self.project_index_file_path)
        os.makedirs(index_dir, exist_ok=True)

        for file_path in self.walk_files(self.ctx.cwd, self.ctx.ignored_files):
            content = read_file(file_path)
            if content:
                formatted_entry = self.format_project_index_file(file_path, content)
                with open(self.project_index_file_path, 'a', encoding='utf-8') as index_file:
                    index_file.write(formatted_entry)

    def format_project_index_file(self, file_path, content):
        return f"{self.seperator}{file_path}{self.seperator}\n{content}{self.seperator}\nEND{self.seperator}\n"
