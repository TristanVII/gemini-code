import os
def read_file(file_path):
    try:
        # Attempt to open and read the file
        with open(file_path, 'r', encoding='utf-8') as f:
             content = f.read()
             # Process content
        return content
    except UnicodeDecodeError:
        print(f"Skipping file with encoding issues: {file_path}")
    except Exception as e:
        print(f"Other error processing file {file_path}: {e}")
        return None


def write_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)


def delete_file(file_path):
    os.remove(file_path)


def create_file(file_path):
    try:
        f = open(file_path, "x")
    except FileExistsError as e:
        print(f"File already exists: {file_path}")
        raise e
    except Exception as e:
        print(f"Error creating file {file_path}: {e}")
        raise e

def get_git_ignore_file(file_path):
    git_ignore_file = os.path.join(file_path, '.gitignore')
    if os.path.exists(git_ignore_file):
        with open(git_ignore_file, 'r') as file:
            return file.read()
    return None

def get_git_ignore_file_content(file_path):
    git_ignore_file = get_git_ignore_file(file_path)
    if git_ignore_file:
        lines = git_ignore_file.split('\n')
        # Filter out comments and empty lines
        return [line for line in lines if line.strip() and not line.strip().startswith('#')]
    return []