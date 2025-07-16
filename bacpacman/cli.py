import os

import click
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import CredentialUnavailableError
from dotenv import set_key

from . import azure_handler, sql_handler, ui


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """A utility for managing Azure SQL databases."""
    if ctx.invoked_subcommand is None:
        ui.run_interactive_workflow()


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
    sql_handler.extract_bacpac(
        server_name, database_name, output_file, auth_method="aad"
    )


@cli.command()
def login() -> None:
    """Authenticates the user with Azure and lists subscriptions."""
    try:
        subscriptions = azure_handler.list_subscriptions()
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
        subscriptions = azure_handler.list_subscriptions()
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

    servers = azure_handler.list_servers(subscription_id)
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

    databases = azure_handler.list_databases(subscription_id, server_name)
    if not databases:
        click.echo("No databases found on the specified server.")
        return

    click.echo("Available databases:")
    for db in databases:
        click.echo(f"- {db.name}")


@cli.command()
@click.option("--input-file", help="The bacpac file to import.")
@click.option(
    "--server-name", help="The name of the local SQL server (defaults to 'localhost')."
)
@click.option("--database-name", help="The name of the target database.")
def import_bacpac(
    input_file: str | None, server_name: str | None, database_name: str | None
) -> None:
    """Imports a bacpac to a local SQL server."""
    if input_file and database_name:
        # If all arguments are provided, run non-interactively
        final_server_name = server_name or "localhost"
        sql_handler.import_bacpac(input_file, final_server_name, database_name)
    else:
        # Otherwise, run the interactive workflow
        ui.run_import_workflow(server_name)
