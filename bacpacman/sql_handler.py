import platform
import shutil
import subprocess
import sys

import click
import keyring
import keyring.errors
import questionary


def extract_bacpac(
    server_name: str,
    database_name: str,
    output_file: str,
    auth_method: str,
    username: str | None = None,
) -> None:
    """The core logic for extracting a bacpac file."""
    questionary.print(
        f"Extracting bacpac from {database_name} on {server_name}...",
        style="bold fg:green",
    )

    command: list[str] = [
        "sqlpackage",
        "/Action:Export",
        f"/SourceServerName:tcp:{server_name}.database.windows.net",
        f"/SourceDatabaseName:{database_name}",
        "/p:VerifyExtraction=False",
    ]

    if auth_method == "aad":
        command.append("/ua:True")
    elif auth_method == "sql" and username:
        try:
            password = keyring.get_password(server_name, username)
            if not password:
                password = questionary.password(
                    f"Enter password for {username} on {server_name}:"
                ).ask()
                if password:
                    keyring.set_password(server_name, username, password)
            if password:
                command.extend(
                    [f"/SourceUser:{username}", f"/SourcePassword:{password}"]
                )
        except keyring.errors.NoKeyringError:
            questionary.print(
                "Error: No keyring backend found. Please install a backend for your OS "
                "(e.g., 'secretstorage' on Linux).",
                style="bold fg:red",
            )
            return

    command.append(f"/TargetFile:{output_file}")

    try:
        questionary.print("Extracting bacpac...", style="bold fg:green")
        process = subprocess.run(
            command, check=True, capture_output=True, text=True, encoding="utf-8"
        )
        questionary.print(
            f"Successfully extracted bacpac to {output_file}", style="bold fg:green"
        )
        if process.stdout:
            questionary.print(process.stdout)
    except FileNotFoundError:
        questionary.print("Error: 'sqlpackage' command not found.", style="bold fg:red")
        questionary.print(
            "Please ensure the sqlpackage utility is installed and in your system's "
            "PATH."
        )
    except subprocess.CalledProcessError as e:
        questionary.print(
            "Error: The 'sqlpackage' command failed.", style="bold fg:red"
        )
        questionary.print(f"Command executed: {' '.join(command)}")
        questionary.print("\n--- sqlpackage error output ---", style="bold fg:yellow")
        questionary.print(e.stderr, style="fg:yellow")
        questionary.print("-------------------------------", style="bold fg:yellow")


def import_bacpac(input_file: str, server_name: str, database_name: str) -> None:
    """Imports a bacpac to a local SQL server."""
    click.echo(f"Importing {input_file} to {database_name} on {server_name}...")
    command: list[str] = [
        "sqlpackage",
        "/Action:Import",
        f"/SourceFile:{input_file}",
        f"/TargetServerName:{server_name}",
        f"/TargetDatabaseName:{database_name}",
    ]
    try:
        subprocess.run(command, check=True)
        click.echo(f"Successfully imported {input_file} to {database_name}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        click.echo(f"Error importing bacpac: {e}")
        click.echo("Please ensure 'sqlpackage' is installed and in your PATH.")


def check_sqlpackage() -> None:
    """
    Checks if sqlpackage is in the PATH and provides installation instructions if not.
    """
    if not shutil.which("sqlpackage"):
        click.echo(
            "The 'sqlpackage' command-line utility is not installed or not in your "
            "PATH."
        )
        click.echo(
            "The download page is here: "
            "https://learn.microsoft.com/en-us/sql/tools/sqlpackage/sqlpackage-download?view=sql-server-ver17"
        )

        os_name = platform.system()
        if os_name == "Darwin":
            click.echo("To install it on macOS, you can use the .NET tool.")
            click.echo("\n.NET Tool (requires .NET SDK):")
            click.echo(
                "  Install the .NET SDK from: https://dotnet.microsoft.com/en-us/download"
            )
            click.echo("  Then run: dotnet tool install -g microsoft.sqlpackage")
        elif os_name == "Linux":
            click.echo("To install it on Linux, download the zip file from:")
            click.echo(
                "  https://learn.microsoft.com/en-us/sql/tools/sqlpackage/sqlpackage-download#linux"
            )
        elif os_name == "Windows":
            click.echo(
                "To install it on Windows, download the DacFramework.msi installer "
                "from:"
            )
            click.echo(
                "  https://learn.microsoft.com/en-us/sql/tools/sqlpackage/sqlpackage-download#windows"
            )

        sys.exit(1)
