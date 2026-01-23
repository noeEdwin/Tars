import os

class TarsHands:
    """A collection of tools for TARS to interact with the local filesystem."""


    def __init__(self, home_dir="/home/lancelot"):
        self.home = Path(home_dir).resolve()
        self.blacklist = {
            'snap', 'miniconda3', 'anaconda3', 'site-packages', 
            '.git', '__pycache__', 'node_modules', 'etc', 'bin', 
            'root', '.ssh', '.gnupg'
        }

    def _is_safe(self, target_path: str) -> bool:
        """It verifies if the rout is safe and it's not in the blacklist"""
        try:
            target = Path(target_path).resolve()
            if not target.is_relative_to(self.home):
                return False
            if any(part in self.blacklist for part in target.parts):
                return False
            return True
        except Exception:
            return False

    @staticmethod
    def list_files(path: str):
        """Returns a list of files in a specific directory. 
        Use this after finding a path in the System Map."""
        try:
            return os.listdir(path)
        except Exception as e:
            return f"Error accessing {path}: {str(e)}"

    @staticmethod
    def read_code(path: str):
        """Reads the content of a file. Use this to analyze scripts or notes."""
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading {path}: {str(e)}"

    @staticmethod
    def create_file(path: str, content: str = ""):
        """Creates a new file with optional content."""
        try:
            with open(path, 'w') as f:
                f.write(content)
            return f"File created successfully at {path}"
        except Exception as e:
            return f"Error creating file: {str(e)}"


    @staticmethod
    def update_file(path: str, content: str, mode: str = "append"):
        """Updates an existing file. Mode can be 'append' or 'overwrite'."""
        try:
            write_mode = 'a' if mode == "append" else 'w'
            with open(path, write_mode) as f:
                f.write(content)
            return f"File updated ({mode}) at {path}"
        except Exception as e:
            return f"Error updating file: {str(e)}"

    @staticmethod
    def delete_path(path: str):
        """Safely removes a file or an entire directory tree."""
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                return f"Directory {path} and all contents deleted."
            else:
                os.remove(path)
                return f"File {path} deleted."
        except Exception as e:
            return f"Error deleting path: {str(e)}"

    
    @staticmethod
    def move_path(src: str, dst: str):
        """Moves or renames a file/directory to a new location."""
        try:
            shutil.move(src, dst)
            return f"Moved {src} to {dst}"
        except Exception as e:
            return f"Error moving path: {str(e)}"

    @staticmethod
    def create_directory(path: str):
        """Creates a directory and any necessary parent directories."""
        try:
            os.makedirs(path, exist_ok=True)
            return f"Directory structure {path} ensured."
        except Exception as e:
            return f"Error creating directory: {str(e)}"