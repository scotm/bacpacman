#!/usr/bin/env python3
import contextlib
import os
import platform
import shutil
import subprocess
import sys

import click
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import CredentialUnavailableError, DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient, SubscriptionClient
from azure.mgmt.sql import SqlManagementClient
from dotenv import load_dotenv, set_key

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


def _extract_bacpac_logic(
    server_name: str, database_name: str, output_file: str
) -> None:
    """The core logic for extracting a bacpac file."""
    click.echo(f"Extracting bacpac from {database_name} on {server_name}...")
    command: list[str] = [
        "sqlpackage",
        "/Action:Export",
        f"/SourceServerName:{server_name}.database.windows.net",
        f"/SourceDatabaseName:{database_name}",
        f"/TargetFile:{output_file}",
        "/p:Storage=Memory",
        "/p:Authentication=ActiveDirectoryInteractive",
    ]
    try:
        subprocess.run(command, check=True)
        click.echo(f"Successfully extracted bacpac to {output_file}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        click.echo(f"Error extracting bacpac: {e}")
        click.echo("Please ensure 'sqlpackage' is installed and in your PATH.")


def full_workflow() -> None:
    """Runs the full end-to-end workflow."""
    click.echo("Starting the full BacPacman workflow...")

    # 1. Login
    try:
        subscription_client = get_subscription_client()
        with open(os.devnull, "w") as f, contextlib.redirect_stderr(f):
            subscriptions = list(subscription_client.subscriptions.list())
        if not subscriptions:
            click.echo(
                "No subscriptions found. "
                "Please ensure you have access to at least one subscription."
            )
            return
    except (CredentialUnavailableError, ClientAuthenticationError):
        click.echo(
            "Authentication failed. "
            "Your Azure credentials may have expired or are invalid."
        )
        click.echo(
            "Please run 'az login --scope https://management.azure.com/.default' "
            "to authenticate."
        )
        return

    # 2. Select Subscription
    for i, sub in enumerate(subscriptions):
        click.echo(f"{i+1}. {sub.display_name} ({sub.subscription_id})")
    sub_index = click.prompt(
        "Please enter the number of the subscription to use", type=int
    )
    subscription_id = subscriptions[sub_index - 1].subscription_id
    set_key(".env", "AZURE_SUBSCRIPTION_ID", subscription_id)
    click.echo(f"Selected subscription: {subscription_id}")

    # 3. List and Select Server
    sql_client = get_sql_client(subscription_id)
    servers = list(sql_client.servers.list())
    if not servers:
        click.echo("No SQL servers found in the selected subscription.")
        return

    click.echo("Available SQL servers:")
    for i, server in enumerate(servers):
        click.echo(f"{i+1}. {server.name}")
    server_index = click.prompt(
        "Please enter the number of the server to use", type=int
    )
    selected_server = servers[server_index - 1]

    # 4. List and Select Database
    resource_group_name = selected_server.id.split("/")[4]

    databases = list(
        sql_client.databases.list_by_server(resource_group_name, selected_server.name)
    )
    if not databases:
        click.echo("No databases found on the specified server.")
        return

    click.echo("Available databases:")
    for i, db in enumerate(databases):
        click.echo(f"{i+1}. {db.name}")
    db_index = click.prompt("Please enter the number of the database to use", type=int)
    selected_database = databases[db_index - 1]

    # 5. Extract Bacpac
    output_file = f"{selected_database.name}.bacpac"
    _extract_bacpac_logic(selected_server.name, selected_database.name, output_file)


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
    _extract_bacpac_logic(server_name, database_name, output_file)


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
    servers = list(sql_client.servers.list())

    if not servers:
        click.echo("No SQL servers found in the selected subscription.")
        return

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
    # This is a simplification, assuming the server is in the first resource group found
    resource_groups = list(get_resource_client(subscription_id).resource_groups.list())
    if not resource_groups:
        click.echo("No resource groups found in the subscription.")
        return
    resource_group_name = resource_groups[0].name

    databases = list(
        sql_client.databases.list_by_server(resource_group_name, server_name)
    )

    if not databases:
        click.echo("No databases found on the specified server.")
        return

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


if __name__ == "__main__":
    check_sqlpackage()
    if len(sys.argv) == 1:
        full_workflow()
    else:
        cli()
