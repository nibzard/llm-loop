# dev_tools.py
import subprocess
import pathlib
import shutil

def write_file(file_path: str, content: str) -> str:
    """
    Writes or overwrites content to the specified file.
    Creates directories if they don't exist.
    Returns a success message or an error string.
    """
    try:
        p = pathlib.Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return (f"✅ File '{file_path}' written successfully "
                f"({len(content)} characters).")
    except Exception as e:
        return f"❌ Error writing file '{file_path}': {str(e)}"

def read_file(file_path: str) -> str:
    """
    Reads and returns the content of the specified file.
    Returns an error message if the file cannot be read.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            return (f"📄 File '{file_path}' content "
                    f"({len(content)} characters):\n\n{content}")
    except FileNotFoundError:
        return f"❌ File '{file_path}' not found."
    except Exception as e:
        return f"❌ Error reading file '{file_path}': {str(e)}"

def list_directory(path: str = ".") -> str:
    """
    Lists files and directories in the specified path (default: current
    directory). Returns a formatted list of items or an error message.
    """
    try:
        p = pathlib.Path(path)
        if not p.exists():
            return f"❌ Directory '{path}' does not exist."

        items = list(p.iterdir())
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
    except Exception as e:
        return f"❌ Error listing directory '{path}': {str(e)}"

def run_shell_command(command: str) -> str:
    """
    Executes a shell command and returns its stdout and stderr.
    CAUTION: This tool can execute arbitrary commands. Use with extreme care
    and approval. Returns a string containing stdout and stderr, or an error
    message.
    """
    try:
        process = subprocess.run(
            command,
            shell=True,
            check=False,  # Don't raise exception for non-zero exit codes
            capture_output=True,
            text=True,
            timeout=30  # Add a timeout
        )

        output = f"💻 COMMAND: {command}\n"
        if process.stdout:
            output += f"📤 STDOUT:\n{process.stdout}\n"
        else:
            output += "📤 STDOUT: (empty)\n"
        if process.stderr:
            output += f"⚠️  STDERR:\n{process.stderr}\n"
        output += f"🔢 RETURN CODE: {process.returncode}"

        return output
    except subprocess.TimeoutExpired:
        return (f"⏰ Error: Command '{command}' timed out after 30 "
                f"seconds.")
    except Exception as e:
        return f"❌ Error running command '{command}': {str(e)}"

def create_directory(dir_path: str) -> str:
    """
    Creates a directory (and parent directories if needed).
    Returns a success message or an error string.
    """
    try:
        p = pathlib.Path(dir_path)
        p.mkdir(parents=True, exist_ok=True)
        return f"✅ Directory '{dir_path}' created successfully."
    except Exception as e:
        return f"❌ Error creating directory '{dir_path}': {str(e)}"

def delete_file_or_directory(path: str) -> str:
    """
    Deletes a file or directory.
    CAUTION: This permanently removes files/directories.
    Returns a success message or an error string.
    """
    try:
        p = pathlib.Path(path)
        if not p.exists():
            return f"⚠️  Path '{path}' does not exist."

        if p.is_file():
            p.unlink()
            return f"✅ File '{path}' deleted successfully."
        elif p.is_dir():
            shutil.rmtree(p)
            return f"✅ Directory '{path}' and its contents deleted successfully."
        else:
            return f"❌ Path '{path}' is neither a file nor directory."
    except Exception as e:
        return f"❌ Error deleting '{path}': {str(e)}"

def file_exists(file_path: str) -> str:
    """
    Checks if a file or directory exists.
    Returns a status message.
    """
    p = pathlib.Path(file_path)
    if p.exists():
        if p.is_file():
            size = p.stat().st_size
            return f"✅ File '{file_path}' exists ({size} bytes)."
        elif p.is_dir():
            items = len(list(p.iterdir()))
            return f"✅ Directory '{file_path}' exists ({items} items)."
        else:
            return f"✅ Path '{file_path}' exists (special file type)."
    else:
        return f"❌ Path '{file_path}' does not exist."

def current_working_directory() -> str:
    """
    Returns the current working directory.
    """
    return f"📂 Current working directory: {pathlib.Path.cwd()}"

def install_python_package(package_name: str) -> str:
    """
    Installs a Python package using pip.
    Returns the installation result.
    """
    try:
        process = subprocess.run(
            ["pip", "install", package_name],
            capture_output=True,
            text=True,
            timeout=120  # Longer timeout for installations
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
        return f"⏰ Package installation '{package_name}' timed out after 120 seconds."
    except Exception as e:
        return f"❌ Error installing package '{package_name}': {str(e)}"