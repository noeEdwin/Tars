import os
from pathlib import Path
import shutil
import pymupdf
from docx import Document
import subprocess
import tiktoken
import re

class TarsHands:
    """A collection of tools for TARS to interact with the local filesystem."""
    @staticmethod
    def clean_text(text: str) -> str:
        """Elimina ruido innecesario para ahorrar tokens."""
        # Elimina múltiples saltos de línea y espacios en blanco extra
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r' +', ' ', text)
        # Elimina URLs básicas y pies de página comunes 
        text = re.sub(r'http\S+', '', text)
        return text.strip()

    @staticmethod
    def count_tokens(text: str, model="gpt-4o") -> int:
        """Calcula cuántos tokens consume el texto realmente."""
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))

    @staticmethod
    def read_document(path: str, max_tokens: int = 4000):
        """It extract information from files PDF, DOCX o TXT."""
        ext = Path(path).suffix.lower()
        content = ""
        try:
            if ext == ".pdf":
                with pymupdf.open(path) as doc:
                    # Extraemos solo texto relevante
                    content = "\n".join([page.get_text("text") for page in doc])
            elif ext == ".docx":
                doc = Document(path)
                content = "\n".join([p.text for p in doc.paragraphs])
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

            cleaned_content = TarsHands.clean_text(content)
            num_tokens = TarsHands.count_tokens(cleaned_content)
            if num_tokens > max_tokens:
                print(f"⚠️ Alerta: Documento de {num_tokens} tokens. Recortando a {max_tokens}.")
                return cleaned_content[:max_tokens * 4]

            return cleaned_content
        except Exception as e:
            return f"Error al leer el documento {ext}: {str(e)}"

    @staticmethod
    def execute_command(command: str):
        """Ejecuta comandos en la terminal del servidor (usar con precaución)."""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        except Exception as e:
            return f"Error de ejecución: {str(e)}"

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
        """Returns a list of files in a specific directory, marking them as [FILE] or [DIR]."""
        try:
            items = os.listdir(path)
            detailed_list = []
            for item in items:
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    detailed_list.append(f"[DIR]  {item}")
                else:
                    detailed_list.append(f"[FILE] {item}")
            return detailed_list
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