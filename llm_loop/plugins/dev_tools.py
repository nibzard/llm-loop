"""Built-in development tools for LLM Loop (validated and simple)."""

import pathlib
import shutil
import subprocess

from ..utils.validation import sanitize_command, validate_path
from ..utils.exceptions import ValidationError


def write_file(file_path: str, content: str) -> str:
    """Write or overwrite a file, creating parent directories if needed."""
    try:
        validated_path = validate_path(file_path)
        validated_path.parent.mkdir(parents=True, exist_ok=True)
        with open(validated_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ File '{file_path}' written successfully ({len(content)} characters)."
    except ValidationError as e:
        return f"❌ Validation error for '{file_path}': {e}"
    except Exception as e:
        return f"❌ Error writing file '{file_path}': {e}"


def read_file(file_path: str) -> str:
    """Read and return file contents."""
    try:
        validated_path = validate_path(file_path)
        with open(validated_path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"📄 File '{file_path}' content ({len(content)} characters):\n\n{content}"
    except ValidationError as e:
        return f"❌ Validation error for '{file_path}': {e}"
    except FileNotFoundError:
        return f"❌ File '{file_path}' not found."
    except Exception as e:
        return f"❌ Error reading file '{file_path}': {e}"


def list_directory(path: str = ".") -> str:
    """List files and directories in a path."""
    try:
        validated_path = validate_path(path)
        if not validated_path.exists():
            return f"❌ Directory '{path}' does not exist."

        items = list(validated_path.iterdir())
        if not items:
            return f"📁 Directory '{path}' is empty."

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


def run_shell_command(command: str, timeout: int = 30) -> str:
    """Execute a sanitized shell command and return stdout/stderr."""
    try:
        sanitized_command = sanitize_command(command)
        process = subprocess.run(
            sanitized_command,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = f"💻 COMMAND: {sanitized_command}\n"
        output += f"📤 STDOUT:\n{process.stdout}\n" if process.stdout else "📤 STDOUT: (empty)\n"
        if process.stderr:
            output += f"⚠️  STDERR:\n{process.stderr}\n"
        output += f"🔢 RETURN CODE: {process.returncode}"
        return output
    except ValidationError as e:
        return f"❌ Command validation error: {e}"
    except subprocess.TimeoutExpired:
        return f"⏰ Error: Command '{command}' timed out after {timeout} seconds."
    except Exception as e:
        return f"❌ Error running command '{command}': {e}"


def create_directory(dir_path: str) -> str:
    """Create a directory (with parents)."""
    try:
        validated_path = validate_path(dir_path)
        validated_path.mkdir(parents=True, exist_ok=True)
        return f"✅ Directory '{dir_path}' created successfully."
    except ValidationError as e:
        return f"❌ Validation error for '{dir_path}': {e}"
    except Exception as e:
        return f"❌ Error creating directory '{dir_path}': {e}"


def delete_file_or_directory(path: str) -> str:
    """Delete a file or directory tree."""
    try:
        validated_path = validate_path(path)
        if not validated_path.exists():
            return f"⚠️  Path '{path}' does not exist."
        if validated_path.is_file():
            validated_path.unlink()
            return f"✅ File '{path}' deleted successfully."
        if validated_path.is_dir():
            shutil.rmtree(validated_path)
            return f"✅ Directory '{path}' and its contents deleted successfully."
        return f"❌ Path '{path}' is neither a file nor directory."
    except ValidationError as e:
        return f"❌ Validation error for '{path}': {e}"
    except Exception as e:
        return f"❌ Error deleting '{path}': {e}"


def file_exists(file_path: str) -> str:
    """Check if a path exists and report details."""
    try:
        validated_path = validate_path(file_path)
        if validated_path.exists():
            if validated_path.is_file():
                size = validated_path.stat().st_size
                return f"✅ File '{file_path}' exists ({size} bytes)."
            if validated_path.is_dir():
                items = len(list(validated_path.iterdir()))
                return f"✅ Directory '{file_path}' exists ({items} items)."
            return f"✅ Path '{file_path}' exists (special file type)."
        return f"❌ Path '{file_path}' does not exist."
    except ValidationError as e:
        return f"❌ Validation error for '{file_path}': {e}"
    except Exception as e:
        return f"❌ Error checking '{file_path}': {e}"


def current_working_directory() -> str:
    """Return the current working directory."""
    return f"📂 Current working directory: {pathlib.Path.cwd()}"


def install_python_package(package_name: str, timeout: int = 120) -> str:
    """Install a Python package via pip (best used with approval)."""
    if not package_name or not package_name.replace("-", "").replace("_", "").replace(".", "").isalnum():
        return f"❌ Invalid package name: {package_name}"
    try:
        process = subprocess.run(
            ["pip", "install", package_name],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = f"📦 Installing package: {package_name}\n"
        if process.returncode == 0:
            output += f"✅ Successfully installed {package_name}\n"
        else:
            output += f"❌ Failed to install {package_name}\n"
        if process.stdout:
            output += f"📤 STDOUT:\n{process.stdout}\n"
        if process.stderr:
            output += f"⚠️  STDERR:\n{process.stderr}\n"
        output += f"🔢 RETURN CODE: {process.returncode}"
        return output
    except subprocess.TimeoutExpired:
        return f"⏰ Package installation '{package_name}' timed out after {timeout} seconds."
    except Exception as e:
        return f"❌ Error installing package '{package_name}': {e}"
