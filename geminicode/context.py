class Context:
    """ Holds stuff like cwd, i
    ignored files, max tokens, max iteration, model, stuff passed in as flags.
    """
    def __init__(self, cwd):
        self.cwd = cwd
        self.ignored_files = ['.git', '.gitignore', '.geminicode', 'system_prompts']
