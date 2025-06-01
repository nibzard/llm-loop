"""Secure development tools for LLM Loop."""

import subprocess
import pathlib
import shutil
from typing import Optional

from ..utils.types import ToolResult
from ..utils.validation import validate_path, sanitize_command
from ..utils.exceptions import ToolExecutionError, ValidationError


class SecureFileOperations:
    """Secure file operations with input validation."""

    @staticmethod
    def write_file(file_path: str, content: str) -> str:
        """
        Writes or overwrites content to the specified file.
        Creates directories if they don't exist.
        Returns a success message or an error string.
        """
        try:
            validated_path = validate_path(file_path)
            validated_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(validated_path, "w", encoding="utf-8") as f:
                f.write(content)
            return (f"✅ File '{file_path}' written successfully "
                    f"({len(content)} characters).")
        except ValidationError as e:
            return f"❌ Validation error for '{file_path}': {e}"
        except Exception as e:
            return f"❌ Error writing file '{file_path}': {e}"

    @staticmethod
    def read_file(file_path: str) -> str:
        """
        Reads and returns the content of the specified file.
        Returns an error message if the file cannot be read.
        """
        try:
            validated_path = validate_path(file_path)
            with open(validated_path, "r", encoding="utf-8") as f:
                content = f.read()
                return (f"📄 File '{file_path}' content "
                        f"({len(content)} characters):\n\n{content}")
        except ValidationError as e:
            return f"❌ Validation error for '{file_path}': {e}"
        except FileNotFoundError:
            return f"❌ File '{file_path}' not found."
        except Exception as e:
            return f"❌ Error reading file '{file_path}': {e}"

    @staticmethod
    def list_directory(path: str = ".") -> str:
        """
        Lists files and directories in the specified path (default: current
        directory). Returns a formatted list of items or an error message.
        """
        try:
            validated_path = validate_path(path)
            if not validated_path.exists():
                return f"❌ Directory '{path}' does not exist."

            items = list(validated_path.iterdir())
            if not items:
                return f"📁 Directory '{path}' is empty."

            # Sort and categorize
            dirs = [item for item in items if item.is_dir()]
            files = [item for item in items if item.is_file()]

            result = f"📁 Directory '{path}' contents:\n\n"

            if dirs:
                result += "📂 Directories:\n"
                for d in sorted(dirs):
                    result += f"  📂 {d.name}/\n"
                result += "\n"

            if files:
                result += "📄 Files:\n"
                for f in sorted(files):
                    size = f.stat().st_size
                    result += f"  📄 {f.name} ({size} bytes)\n"

            return result
        except ValidationError as e:
            return f"❌ Validation error for '{path}': {e}"
        except Exception as e:
            return f"❌ Error listing directory '{path}': {e}"

    @staticmethod
    def run_shell_command(command: str, timeout: int = 30) -> str:
        """
        Executes a shell command and returns its stdout and stderr.
        CAUTION: This tool can execute arbitrary commands. Use with extreme care
        and approval. Returns a string containing stdout and stderr, or an error
        message.
        """
        try:
            sanitized_command = sanitize_command(command)
            
            process = subprocess.run(
                sanitized_command,
                shell=True,
                check=False,  # Don't raise exception for non-zero exit codes
                capture_output=True,
                text=True,
                timeout=timeout
            )

            output = f"💻 COMMAND: {sanitized_command}\n"
            if process.stdout:
                output += f"📤 STDOUT:\n{process.stdout}\n"
            else:
                output += "📤 STDOUT: (empty)\n"
            if process.stderr:
                output += f"⚠️  STDERR:\n{process.stderr}\n"
            output += f"🔢 RETURN CODE: {process.returncode}"

            return output
        except ValidationError as e:
            return f"❌ Command validation error: {e}"
        except subprocess.TimeoutExpired:
            return (f"⏰ Error: Command '{command}' timed out after {timeout} "
                    f"seconds.")
        except Exception as e:
            return f"❌ Error running command '{command}': {e}"

    @staticmethod
    def create_directory(dir_path: str) -> str:
        """
        Creates a directory (and parent directories if needed).
        Returns a success message or an error string.
        """
        try:
            validated_path = validate_path(dir_path)
            validated_path.mkdir(parents=True, exist_ok=True)
            return f"✅ Directory '{dir_path}' created successfully."
        except ValidationError as e:
            return f"❌ Validation error for '{dir_path}': {e}"
        except Exception as e:
            return f"❌ Error creating directory '{dir_path}': {e}"

    @staticmethod
    def delete_file_or_directory(path: str) -> str:
        """
        Deletes a file or directory.
        CAUTION: This permanently removes files/directories.
        Returns a success message or an error string.
        """
        try:
            validated_path = validate_path(path)
            if not validated_path.exists():
                return f"⚠️  Path '{path}' does not exist."

            if validated_path.is_file():
                validated_path.unlink()
                return f"✅ File '{path}' deleted successfully."
            elif validated_path.is_dir():
                shutil.rmtree(validated_path)
                return f"✅ Directory '{path}' and its contents deleted successfully."
            else:
                return f"❌ Path '{path}' is neither a file nor directory."
        except ValidationError as e:
            return f"❌ Validation error for '{path}': {e}"
        except Exception as e:
            return f"❌ Error deleting '{path}': {e}"

    @staticmethod
    def file_exists(file_path: str) -> str:
        """
        Checks if a file or directory exists.
        Returns a status message.
        """
        try:
            validated_path = validate_path(file_path)
            if validated_path.exists():
                if validated_path.is_file():
                    size = validated_path.stat().st_size
                    return f"✅ File '{file_path}' exists ({size} bytes)."
                elif validated_path.is_dir():
                    items = len(list(validated_path.iterdir()))
                    return f"✅ Directory '{file_path}' exists ({items} items)."
                else:
                    return f"✅ Path '{file_path}' exists (special file type)."
            else:
                return f"❌ Path '{file_path}' does not exist."
        except ValidationError as e:
            return f"❌ Validation error for '{file_path}': {e}"
        except Exception as e:
            return f"❌ Error checking '{file_path}': {e}"

    @staticmethod
    def current_working_directory() -> str:
        """
        Returns the current working directory.
        """
        return f"📂 Current working directory: {pathlib.Path.cwd()}"

    @staticmethod
    def install_python_package(package_name: str, timeout: int = 120) -> str:
        """
        Installs a Python package using pip.
        Returns the installation result.
        """
        # Basic validation for package name
        if not package_name or not package_name.replace("-", "").replace("_", "").replace(".", "").isalnum():
            return f"❌ Invalid package name: {package_name}"
            
        try:
            process = subprocess.run(
                ["pip", "install", package_name],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            output = f"📦 Installing package: {package_name}\n"
            if process.returncode == 0:
                output += f"✅ Successfully installed {package_name}\n"
            else:
                output += f"❌ Failed to install {package_name}\n"

            output += f"📤 STDOUT:\n{process.stdout}\n" if process.stdout else ""
            if process.stderr:
                output += f"⚠️  STDERR:\n{process.stderr}\n"
            output += f"🔢 RETURN CODE: {process.returncode}"

            return output
        except subprocess.TimeoutExpired:
            return f"⏰ Package installation '{package_name}' timed out after {timeout} seconds."
        except Exception as e:
            return f"❌ Error installing package '{package_name}': {e}"


# Legacy function exports for backward compatibility
write_file = SecureFileOperations.write_file
read_file = SecureFileOperations.read_file
list_directory = SecureFileOperations.list_directory
run_shell_command = SecureFileOperations.run_shell_command
create_directory = SecureFileOperations.create_directory
delete_file_or_directory = SecureFileOperations.delete_file_or_directory
file_exists = SecureFileOperations.file_exists
current_working_directory = SecureFileOperations.current_working_directory
install_python_package = SecureFileOperations.install_python_package