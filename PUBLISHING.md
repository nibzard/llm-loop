# Publishing Guide

This guide outlines the steps to publish the `llm-loop-plugin` package to TestPyPI for testing and then to the official PyPI repository for public release.

## Prerequisites

1.  **Install necessary tools**:
    If you don't have them already, install `build` and `twine`:
    ```bash
    pip install build twine
    ```

2.  **PyPI and TestPyPI Accounts**:
    Ensure you have accounts on both [PyPI](https://pypi.org/) and [TestPyPI](https://test.pypi.org/).

3.  **API Tokens**:
    It's recommended to use API tokens for uploading packages.
    *   Generate an API token on TestPyPI (scoped to your project or all projects).
    *   Generate an API token on PyPI (scoped to your project or all projects).
    *   You can configure `twine` to use these tokens, for example, by using a `~/.pypirc` file or by entering `__token__` as the username and the token value as the password when prompted by `twine`.

    Example `~/.pypirc` configuration:
    ```ini
    [testpypi]
    username = __token__
    password = pypi-your-testpypi-token

    [pypi]
    username = __token__
    password = pypi-your-pypi-token
    ```

## Step-by-Step Publishing Workflow

### 1. Update Version Number

*   Before publishing a new version, ensure the `version` in `pyproject.toml` is updated according to [semantic versioning](https://semver.org/) (e.g., `0.2.1` -> `0.2.2` or `0.3.0`).
    ```toml
    # pyproject.toml
    [project]
    name = "llm-loop-plugin"
    version = "NEW_VERSION_HERE"
    # ... other fields
    ```

### 2. Clean Previous Builds

*   Remove any old build artifacts from the `dist/` directory to ensure a clean build:
    ```bash
    rm -rf dist
    ```

### 3. Build the Package

*   Build the source archive and wheel for your package:
    ```bash
    python -m build
    ```
    This will create new files in the `dist/` directory (e.g., `llm_loop_plugin-NEW_VERSION_HERE-py3-none-any.whl` and `llm_loop_plugin-NEW_VERSION_HERE.tar.gz`).

### 4. Publish to TestPyPI

*   Upload your package to TestPyPI to ensure everything works as expected:
    ```bash
    python -m twine upload --repository testpypi dist/*
    ```
*   If you encounter issues, use the `--verbose` flag for more detailed output:
    ```bash
    python -m twine upload --repository testpypi --verbose dist/*
    ```
*   **Common Issues & Debugging**:
    *   **Incorrect Version**: If TestPyPI (or PyPI) says the version already exists, ensure you've incremented it in `pyproject.toml` and rebuilt.
    *   **Invalid Classifiers**: If you get an error like `400 'Framework :: Click' is not a valid classifier`, check your classifiers in `pyproject.toml` against the valid list on [PyPI's documentation](https://packaging.python.org/specifications/core-metadata/#trove-classifiers) and remove/correct invalid ones. Rebuild after changes.
    *   **Authentication**: Ensure your TestPyPI token is correctly configured or entered.

### 5. Install from TestPyPI (Recommended Test)

*   It's a good practice to install the package from TestPyPI into a clean virtual environment to verify it works:
    ```bash
    # Optional: Uninstall any existing local/dev version first
    pip uninstall -y llm-loop-plugin

    pip install -i https://test.pypi.org/simple/ llm-loop-plugin==NEW_VERSION_HERE
    ```
    Replace `NEW_VERSION_HERE` with the version you just uploaded. Test its basic functionality.

### 6. Publish to PyPI (Official Release)

*   Once you're confident the package is working correctly (after testing from TestPyPI), upload it to the official PyPI repository.
*   **Important**: Ensure your `dist/` directory contains only the correct, final version files. If you made changes after TestPyPI upload (e.g. bug fixes), repeat steps 1-3.
*   Upload to PyPI:
    ```bash
    python -m twine upload dist/*
    ```
*   For verbose output if issues arise:
    ```bash
    python -m twine upload --verbose dist/*
    ```
*   **Common Issues & Debugging**:
    *   **Project Name Conflict**: If PyPI reports an error like `The user 'your-username' isn't allowed to upload to project 'project-name'`, it might mean the project name is already taken or your account doesn't have permissions for that specific name.
        *   Verify the `name` in `pyproject.toml` is unique and correct.
        *   Ensure the API token you're using has permissions for that project name (or global upload permissions for your account if it's a new project).
    *   **Authentication**: Double-check your PyPI API token. If using a token, remember the username is `__token__`.

### 7. Verify on PyPI

*   After successful upload, visit your project page on PyPI to ensure it looks correct:
    `https://pypi.org/project/llm-loop-plugin/NEW_VERSION_HERE/`

This completes the publishing process!