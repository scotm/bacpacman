import contextlib
import os
import platform
import shutil
import subprocess
import sys
from collections.abc import Iterable
from typing import cast

import click
import keyring
import keyring.errors
import questionary
from azure.core.exceptions import ClientAuthenticationError, ServiceRequestError
from azure.identity import CredentialUnavailableError, DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient, SubscriptionClient
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.sql.models import Database, Server
from dotenv import load_dotenv, set_key
from questionary import Choice

load_dotenv()


def get_credential() -> DefaultAzureCredential:
    """Gets the Azure credential."""
    return DefaultAzureCredential()


def get_subscription_client() -> SubscriptionClient:
    """Gets the subscription client."""
    return SubscriptionClient(get_credential())


def get_resource_client(subscription_id: str) -> ResourceManagementClient:
    """Gets the resource management client."""
    return ResourceManagementClient(get_credential(), subscription_id)


def get_sql_client(subscription_id: str) -> SqlManagementClient:
    """Gets the SQL management client."""
    return SqlManagementClient(get_credential(), subscription_id)


@click.group()
def cli() -> None:
    """A utility for managing Azure SQL databases."""
    pass


# Define a custom style for the prompts
custom_style = questionary.Style(
    [
        ("qmark", "fg:#673ab7 bold"),  # Question mark
        ("question", "bold"),  # Question text
        ("answer", "fg:#f44336 bold"),  # Answer text
        ("pointer", "fg:#673ab7 bold"),  # Pointer character
        ("highlighted", "fg:#673ab7 bold"),  # Highlighted choice
        ("selected", "fg:#ffffff bg:#673ab7"),  # Selected choice
        ("separator", "fg:#cc5454"),  # Separator
        ("instruction", "fg:#858585"),  # Instruction text
        ("text", ""),  # Default text
        ("disabled", "fg:#858585 italic"),  # Disabled choices
    ]
)


def _extract_bacpac_logic(
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
        f"/SourceServerName:'tcp:{server_name}.database.windows.net'",
        f"/SourceDatabaseName:'{database_name}'",
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
                    [f"/SourceUser:'{username}'", f"/SourcePassword:'{password}'"]
                )
        except keyring.errors.NoKeyringError:
            questionary.print(
                "Error: No keyring backend found. Please install a backend for your OS "
                "(e.g., 'secretstorage' on Linux).",
                style="bold fg:red",
            )
            return

    command.append(f"/TargetFile:'{output_file}'")

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


def full_workflow() -> None:
    """Runs the full end-to-end workflow."""
    questionary.print(
        "Starting the full BacPacman workflow...", style="bold fg:#673ab7"
    )

    # 1. Choose Authentication Method
    auth_method_choice = questionary.select(
        "How would you like to authenticate to the database?",
        choices=[
            Choice("Azure Active Directory", "aad"),
            Choice("SQL Server Authentication", "sql"),
        ],
        style=custom_style,
    ).ask()

    if not auth_method_choice:
        return

    selected_server_name: str | None = None
    selected_database_name: str | None = None
    username: str | None = None

    try:
        # 2. Login & Discover Resources via Azure
        questionary.print("Fetching subscriptions...", style="bold")
        subscription_client = get_subscription_client()
        with open(os.devnull, "w") as f, contextlib.redirect_stderr(f):
            subscriptions = list(subscription_client.subscriptions.list())
        if not subscriptions:
            raise ClientAuthenticationError(
                "No subscriptions found. Please ensure you have access to at least one."
            )

        # 3. Select Subscription
        subscription_choices = [
            Choice(
                f"{s.display_name} ({s.subscription_id})",
                s.subscription_id if s.subscription_id else "Unknown",
            )
            for s in subscriptions
        ]
        subscription_id = questionary.select(
            "Select your Azure subscription:",
            choices=subscription_choices,
            style=custom_style,
        ).ask()
        if not subscription_id:
            return
        set_key(".env", "AZURE_SUBSCRIPTION_ID", subscription_id)
        questionary.print(f"Selected subscription: {subscription_id}", style="bold")

        # 4. List and Select Server
        questionary.print("Fetching servers...", style="bold")
        sql_client = get_sql_client(subscription_id)
        servers: Iterable[Server] = cast(Iterable[Server], sql_client.servers.list())
        server_list: list[Server] = list(servers)
        if not server_list:
            questionary.print(
                "No SQL servers found in the selected subscription.",
                style="bold fg:yellow",
            )
            return

        server_choices = [Choice(s.name, s) for s in server_list]
        selected_server: Server | None = questionary.select(
            "Select the SQL server:", choices=server_choices, style=custom_style
        ).ask()
        if not selected_server or not selected_server.name or not selected_server.id:
            return
        selected_server_name = selected_server.name

        # 5. List and Select Database
        questionary.print("Fetching databases...", style="bold")
        resource_group_name = selected_server.id.split("/")[4]
        databases: Iterable[Database] = cast(
            Iterable[Database],
            sql_client.databases.list_by_server(
                resource_group_name, selected_server.name
            ),
        )
        database_list: list[Database] = list(databases)
        if not database_list:
            questionary.print(
                "No databases found on the specified server.", style="bold fg:yellow"
            )
            return

        db_choices = [Choice(db.name, db.name) for db in database_list]
        selected_database_name = questionary.select(
            "Select the database:", choices=db_choices, style=custom_style
        ).ask()
        if not selected_database_name:
            return

    except (ClientAuthenticationError, ServiceRequestError) as e:
        questionary.print(
            f"\nWarning: Could not connect to Azure to discover resources "
            f"({type(e).__name__}).",
            style="bold fg:yellow",
        )
        questionary.print(
            "This can happen due to network issues or if you are not logged in with "
            "'az login'.",
            style="fg:yellow",
        )
        questionary.print("Falling back to manual entry.\n", style="fg:yellow")
        selected_server_name = questionary.text("Enter the server name:").ask()
        selected_database_name = questionary.text("Enter the database name:").ask()

    # 6. Get credentials if using SQL Auth
    if auth_method_choice == "sql":
        if not selected_server_name:
            questionary.print(
                "Server name is required for SQL Authentication.", style="bold fg:red"
            )
            return
        username = questionary.text(
            f"Enter your SQL Server username for '{selected_server_name}':"
        ).ask()

    # 7. Extract Bacpac
    if selected_server_name and selected_database_name:
        output_file = f"{selected_database_name}.bacpac"
        summary = (
            f"Server: {selected_server_name}\n"
            f"Database: {selected_database_name}\n"
            f"Output File: {output_file}"
        )
        questionary.print("\nSummary:", style="bold")
        questionary.print(summary)
        proceed = questionary.confirm("Proceed with the extraction?").ask()
        if proceed:
            _extract_bacpac_logic(
                selected_server_name,
                selected_database_name,
                output_file,
                auth_method_choice,
                username,
            )
        else:
            questionary.print("Extraction cancelled.", style="bold fg:red")


@cli.command()
@click.option("--server-name", prompt="Server Name", help="The name of the SQL server.")
@click.option(
    "--database-name", prompt="Database Name", help="The name of the database."
)
@click.option(
    "--output-file", default="database.bacpac", help="The output file for the bacpac."
)
def extract_bacpac(server_name: str, database_name: str, output_file: str) -> None:
    """Extracts a bacpac from an Azure SQL database."""
    # This command will default to Azure AD authentication.
    _extract_bacpac_logic(server_name, database_name, output_file, auth_method="aad")


@cli.command()
def login() -> None:
    """Authenticates the user with Azure and lists subscriptions."""
    try:
        subscription_client = get_subscription_client()

        # Suppress the verbose error output from the Azure SDK
        with open(os.devnull, "w") as f, contextlib.redirect_stderr(f):
            subscriptions = list(subscription_client.subscriptions.list())

        if not subscriptions:
            click.echo(
                "No subscriptions found. "
                "Please ensure you have access to at least one subscription."
            )
            return

        click.echo("Authentication successful. Available subscriptions:")
        for sub in subscriptions:
            click.echo(f"- {sub.display_name} ({sub.subscription_id})")

    except (CredentialUnavailableError, ClientAuthenticationError):
        click.echo(
            "Authentication failed. "
            "Your Azure credentials may have expired or are invalid."
        )
        click.echo(
            "Please run 'az login --scope https://management.azure.com/.default' "
            "to authenticate."
        )

    except Exception as e:
        click.echo(f"Authentication failed: {e}", err=True)


@cli.command()
@click.option("--subscription-id", help="The ID of the subscription to use.")
def select_subscription(subscription_id: str | None) -> None:
    """Selects an Azure subscription to use."""
    if not subscription_id:
        subscription_client = get_subscription_client()
        subscriptions = list(subscription_client.subscriptions.list())
        for i, sub in enumerate(subscriptions):
            click.echo(f"{i+1}. {sub.display_name} ({sub.subscription_id})")
        sub_index = click.prompt(
            "Please enter the number of the subscription to use", type=int
        )
        if sub_index > 0 and sub_index <= len(subscriptions):
            subscription_id = subscriptions[sub_index - 1].subscription_id

    if subscription_id:
        set_key(".env", "AZURE_SUBSCRIPTION_ID", subscription_id)
        click.echo(f"Selected subscription: {subscription_id}")


@cli.command()
def list_servers() -> None:
    """Lists SQL servers in the selected subscription."""
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    if not subscription_id:
        click.echo("Please select a subscription first using 'select-subscription'.")
        return

    sql_client = get_sql_client(subscription_id)
    servers: Iterable[Server] = cast(Iterable[Server], sql_client.servers.list())

    click.echo("Available SQL servers:")
    for server in servers:
        click.echo(f"- {server.name}")


@cli.command()
@click.option("--server-name", prompt="Server Name", help="The name of the SQL server.")
def list_databases(server_name: str) -> None:
    """Lists databases on a SQL server."""
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    if not subscription_id:
        click.echo("Please select a subscription first using 'select-subscription'.")
        return

    sql_client = get_sql_client(subscription_id)

    # Find the resource group for the given server
    resource_group_name: str | None = None
    try:
        all_servers: Iterable[Server] = cast(
            Iterable[Server], sql_client.servers.list()
        )
        server_details = next((s for s in all_servers if s.name == server_name), None)
        if server_details and server_details.id:
            resource_group_name = server_details.id.split("/")[4]
    except StopIteration:
        click.echo(f"Server '{server_name}' not found in the subscription.")
        return

    if not resource_group_name:
        click.echo(
            f"Could not determine the resource group for server '{server_name}'."
        )
        return

    databases: Iterable[Database] = cast(
        Iterable[Database],
        sql_client.databases.list_by_server(resource_group_name, server_name),
    )

    click.echo("Available databases:")
    for db in databases:
        click.echo(f"- {db.name}")


@cli.command()
@click.option("--input-file", prompt="Input File", help="The bacpac file to import.")
@click.option(
    "--server-name", default="localhost", help="The name of the local SQL server."
)
@click.option(
    "--database-name", prompt="Database Name", help="The name of the target database."
)
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


def check_azure_cli() -> None:
    """Checks if the Azure CLI is in the PATH and provides installation instructions."""
    if not shutil.which("az"):
        click.echo(
            "The 'az' command-line utility is not installed or not in your PATH."
        )
        click.echo(
            "The download page is here: "
            "https://learn.microsoft.com/en-us/cli/azure/install-azure-cli"
        )
        sys.exit(1)


if __name__ == "__main__":
    check_sqlpackage()
    check_azure_cli()
    if len(sys.argv) == 1:
        full_workflow()
    else:
        cli()
