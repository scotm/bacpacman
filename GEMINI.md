# BacPacman Project (GEMINI.md)

This document summarizes the work done, build processes, and other useful information for the BacPacman utility.

## Project Overview

**Objective:** Create a Python command-line utility to simplify the process of managing Azure SQL databases. The core functionality includes authenticating with Azure, selecting a subscription and database, extracting a `.bacpac` file using `sqlpackage`, and subsequently importing it into a local SQL Server instance.

**Core Technologies:**

* **Language:** Python 3
* **Package Manager:** `uv`
* **CLI Framework:** `click`
* **Azure Interaction:** `azure-identity`, `azure-mgmt-resource`, `azure-mgmt-sql`
* **Configuration:** `python-dotenv` for storing the selected subscription ID.
* **Secure Credential Storage:** `keyring` for managing SQL Server passwords in the system keychain.
* **Linting & Formatting:** `ruff` and `black`
* **Type Checking:** `mypy`, `pyright`

## Build & Setup Process

1. **Initialization:** The project was initialized using `uv init`.
2. **Virtual Environment:** A virtual environment was created with `uv venv` and is located in the `.venv` directory.
3. **Activation:** To use the tool or install dependencies, the virtual environment must be activated:

    ```bash
    source .venv/bin/activate
    ```

4. **Dependencies:** All necessary Python packages are defined in `pyproject.toml`. To install both production and development dependencies, run:

    ```bash
    uv pip install .[dev]
    ```

## Implemented Features

* **End-to-End Export Workflow:** The default behavior of the `bacpacman` command is a full, interactive workflow that guides the user through selecting a subscription, server, and database, and then extracts the `.bacpac` file.
* **Smart Import Workflow:** The `bacpacman import-bacpac` command provides a guided workflow that automatically detects `.bacpac` files, suggests database names, and handles local server authentication.
* **Dual Authentication Methods:** The tool supports both Azure Active Directory and SQL Server Authentication for remote exports, and Windows Authentication and SQL Server Authentication for local imports.
* **Secure Credential Management:** The script uses the `keyring` library to securely store and retrieve SQL Server passwords from the operating system's native keychain for both export and import operations.
* **Azure Authentication:** The `login` command uses `DefaultAzureCredential` to authenticate. It requires the user to be logged in via the Azure CLI (`az login`).
* **Prerequisite Checking:** The script checks for the presence of `sqlpackage` and the Azure CLI and provides OS-specific installation instructions if they are missing.
* **Automatic Certificate Handling:** The import command automatically adds `/TargetTrustServerCertificate:True` to the `sqlpackage` command to resolve common connection errors with local SQL Server instances.
* **Typing, Linting, and Formatting:** The entire codebase is fully type-hinted and checked with `mypy`, `pyright`, `ruff`, and `black`.

## Development Tasks

### Linting and Formatting

To format the code with `black`:

```bash
black .
```

To check for linting errors with `ruff`:

```bash
ruff check .
```

To automatically fix linting errors with `ruff`:

```bash
ruff check --fix .
```

### Type Checking

To run `mypy` for static type checking:

```bash
mypy .
```

To run `pyright` for static type checking:

```bash
pyright
```

## How to Run

The recommended way to run the tool is to install it in a virtual environment.

```bash
# Create and activate a virtual environment
uv venv
source .venv/bin/activate

# Install the package in editable mode
uv pip install -e .[dev]

# Run the interactive export workflow
bacpacman

# Run the interactive import workflow
bacpacman import-bacpac
```

## Gemini Added Memories

* Before committing source code to version control, I should first run the formatter, linter, and type-checker, and fix any issues that arise.
* When committing source code, keep commit messages succinct, ideally around 70 characters, but no more than 120 characters.
* When performing git commands, do them one at a time. Do not chain them with double-ampersands.
* When preparing to commit, I will run the formatter, linter, and type-checker. If I make any fixes, I must repeat the entire sequence (format, lint, type-check) until all three tools report zero errors.
* When refactoring a single-file script into a package, the `pyproject.toml` must be updated. The `[project.scripts]` entry point should be changed to `package_name.main:main`, and the `[tool.setuptools]` table should be changed from `py-modules` to `packages = ["package_name"]`.
* `pyright` is a stricter type-checker than `mypy`. When integrating it, a `pyrightconfig.json` file should be created to exclude directories like `.venv` and `build` to avoid analyzing third-party code.
* I should not use the `rm` command to delete files. I will rely on the user to perform file deletions.
* Avoid using `typing.Any` as an escape hatch for type checking. For complex or variable object structures from external libraries, prefer defining a `typing.Protocol` to enforce type safety on the attributes the application actually uses. Use `Any` only as a last resort when rigorous typing is prohibitively difficult.
* When connecting to a local SQL Server instance with `sqlpackage`, the connection may fail due to an untrusted self-signed certificate. This can be resolved by adding the `/TargetTrustServerCertificate:True` flag to the command.
* A good UX pattern for file-based tools is to automatically scan the current directory for relevant files (e.g., `.bacpac`) and, if found, present them as choices to the user to minimize manual input.