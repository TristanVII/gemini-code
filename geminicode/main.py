import os
import time
import sys
from geminicode.context import Context
from geminicode.utils.files import read_file, write_file, delete_file, create_file, get_git_ignore_file_content
from geminicode.work_tree.tree import WorkTree


def main():
    try:
        ctx = Context(os.getcwd())
        print(ctx.cwd)
        tree = WorkTree(ctx)

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting geminicode CLI.")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 