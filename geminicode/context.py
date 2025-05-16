class Context:
    def __init__(self, cwd):
        self.cwd = cwd
        self.ignored_files = ['.git', '.gitignore', '.geminicode', 'system_prompts']
