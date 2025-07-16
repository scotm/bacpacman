# BacPacman

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Your friendly neighborhood utility for exporting Azure SQL databases to `.bacpac` files and importing them locally.

## Overview

Cloning a remote Azure SQL database to a local SQL Server instance is an itch that many developers need to scratch. `bacpacman` is a simple, interactive command-line tool that automates this entire process. It guides you through selecting your Azure subscription, server, and database, and then uses the `sqlpackage` utility to export a `.bacpac` file. It also provides a smart, interactive workflow to import that `.bacpac` into your local SQL Server.

This tool is designed to be a helpful replacement for the Azure Data Studio export wizard, especially with its impending retirement.

## Key Features

*   **Interactive Workflows:** Run `bacpacman` for a guided export from Azure, or `bacpacman import-bacpac` for a smart import to your local server.
*   **Smart File Detection:** The import workflow automatically finds `.bacpac` files in your directory and prompts you to choose.
*   **Intelligent Defaults:** Automatically suggests database names based on the filename, minimizing manual entry.
*   **Secure Credential Management:** Uses `DefaultAzureCredential` for Azure and the system `keyring` for local SQL Server passwords, so you never have to store secrets in plain text.
*   **Smart Prerequisite Checking:** Automatically checks if `sqlpackage` and the Azure CLI are installed and provides OS-specific installation instructions.
*   **Automatic Certificate Handling:** Resolves common connection errors to local SQL Server instances by automatically trusting the server certificate.

## Prerequisites

Before using `bacpacman`, you will need:

1.  **Python 3.10+** and a package manager like `pip` or `uv`.
2.  The **Azure CLI**. You must be logged in via `az login`.
3.  The **`sqlpackage` command-line utility**. The tool will guide you through the installation if it's missing.

## Installation

You can install `bacpacman` directly from PyPI:

```bash
pip install bacpacman
```

## Development

To run the tool from the source code for development, follow these steps:

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/bacpacman.git
    cd bacpacman
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    # Create the virtual environment
    uv venv

    # Activate it (on macOS/Linux)
    source .venv/bin/activate
    ```

3.  **Install the project in editable mode:**

    ```bash
    # Install the package and its development dependencies
    uv pip install -e .[dev]
    ```

## Usage

### Interactive Workflows

The easiest way to use the tool is to run it without any arguments for the two main workflows.

**Export from Azure to a `.bacpac` file:**

```bash
bacpacman
```

**Import a local `.bacpac` file to your SQL Server:**

```bash
bacpacman import-bacpac
```

### Other Commands

You can also use individual commands for more specific tasks.

**Login and list your subscriptions:**

```bash
bacpacman login
```

**Select a subscription to work with:**

```bash
bacpacman select-subscription
```

**List SQL servers in your selected subscription:**

```bash
bacpacman list-servers
```

**List databases on a specific server:**

```bash
bacpacman list-databases --server-name your-server-name
```

**Extract a `.bacpac` file directly (non-interactive):**

```bash
bacpacman extract-bacpac --server-name your-server --database-name your-db
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.