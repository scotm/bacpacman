# BacPacman

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Your friendly neighborhood utility for exporting Azure SQL databases to `.bacpac` files.

## Overview

Cloning a remote Azure SQL database to a local SQL Server instance is an itch that many developers need to scratch. `bacpacman` is a simple, interactive command-line tool that automates this entire process. It guides you through selecting your Azure subscription, server, and database, and then uses the `sqlpackage` utility to extract a `.bacpac` file, ready for local import.

This tool is designed to be a helpful replacement for the Azure Data Studio export wizard, especially with its impending retirement.

## Key Features

*   **Interactive End-to-End Workflow:** Simply run `bacpacman` to be guided through the entire process.
*   **Smart Prerequisite Checking:** Automatically checks if `sqlpackage` is installed and provides OS-specific installation instructions.
*   **Secure Authentication:** Uses `DefaultAzureCredential` to securely authenticate with your Azure account via the Azure CLI.
*   **User-Friendly Prompts:** Gracefully handles expired credentials and other common errors with clear, actionable messages.
*   **Modular Commands:** Provides individual commands for specific actions like listing servers or databases.

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

## Usage

### Default Interactive Workflow

The easiest way to use the tool is to run it without any arguments. This will start the interactive workflow that guides you through every step.

```bash
bacpacman
```

### Individual Commands

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

**Extract a `.bacpac` file directly:**
```bash
bacpacman extract-bacpac --server-name your-server --database-name your-db
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
