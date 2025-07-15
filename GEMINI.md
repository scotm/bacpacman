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

* **End-to-End Workflow:** The default behavior of the script is now a full, interactive workflow that guides the user through the entire process of selecting a subscription, server, and database, and then extracts the `.bacpac` file.
* **Dual Authentication Methods:** The tool now supports both `Azure Active Directory` and `SQL Server Authentication`, prompting the user to choose their preferred method.
* **Secure Credential Management:** For SQL Server Authentication, the script uses the `keyring` library to securely store and retrieve passwords from the operating system's native keychain.
* **Azure Authentication:** `login` command that uses `DefaultAzureCredential` to authenticate. It requires the user to be logged in via the Azure CLI (`az login`). The tool now provides user-friendly error messages for common authentication failures.
* **Subscription Management:**
  * `login` automatically lists available subscriptions upon successful authentication.
  * `select-subscription` command allows the user to choose a subscription either by providing the ID or selecting from an interactive list. The chosen ID is stored in a `.env` file.
* **Database Discovery:**
  * `list-servers` command to list all SQL servers within the selected subscription.
  * `list-databases` command to list all databases on a specified server.
* **Bacpac Operations:**
  * `extract-bacpac` command that constructs and executes a `sqlpackage` command to export a database to a `.bacpac` file.
  * `import-bacpac` command that uses `sqlpackage` to import a `.bacpac` file into a local SQL server.
* **`sqlpackage` Prerequisite Check:** The script now checks for the presence of the `sqlpackage` utility on the system's PATH and provides OS-specific installation instructions if it's missing.
* **Typing:** The entire codebase is fully type-hinted for improved clarity and robustness.
* **Linting and Formatting:** The project is configured with `ruff` for linting and `black` for code formatting.

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

## Prerequisites for Use

1. **Python 3** and the **`uv`** package manager must be installed.
2. The **Azure CLI** must be installed, and the user must be authenticated using `az login`.
3. The **`sqlpackage`** command-line utility must be installed and available in the system's PATH.

## How to Run

The main script `bacpacman.py` is executable.

```bash
# First, ensure you are in the virtual environment
source .venv/bin/activate

# Run the end-to-end workflow
./bacpacman.py

# Run a specific command
./bacpacman.py <command> [options]
```

## Gemini Added Memories

* Before committing source code to version control, I should first run the formatter, linter, and type-checker, and fix any issues that arise.
* When committing source code, keep commit messages succinct, ideally around 70 characters, but no more than 120 characters.
* When performing git commands, do them one at a time. Do not chain them with double-ampersands.
* When preparing to commit, I will run the formatter, linter, and type-checker. If I make any fixes, I must repeat the entire sequence (format, lint, type-check) until all three tools report zero errors.
