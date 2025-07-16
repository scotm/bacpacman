import contextlib
import os
import shutil
import sys
from collections.abc import Iterable
from typing import Any, cast

import click
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient, SubscriptionClient
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.sql.models import Database, Server


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


def list_subscriptions() -> list[Any]:
    """Lists all available Azure subscriptions."""
    subscription_client = get_subscription_client()
    with open(os.devnull, "w") as f, contextlib.redirect_stderr(f):
        subscriptions = list(subscription_client.subscriptions.list())
    if not subscriptions:
        raise ClientAuthenticationError(
            "No subscriptions found. Please ensure you have access to at least one."
        )
    return subscriptions


def list_servers(subscription_id: str) -> Iterable[Server]:
    """Lists all SQL servers in a subscription."""
    sql_client = get_sql_client(subscription_id)
    return cast(Iterable[Server], sql_client.servers.list())


def list_databases(subscription_id: str, server_name: str) -> Iterable[Database]:
    """Lists all databases on a SQL server."""
    sql_client = get_sql_client(subscription_id)
    try:
        all_servers = list_servers(subscription_id)
        server_details = next((s for s in all_servers if s.name == server_name), None)
        if server_details and server_details.id:
            resource_group_name = server_details.id.split("/")[4]
            return cast(
                Iterable[Database],
                sql_client.databases.list_by_server(resource_group_name, server_name),
            )
    except StopIteration:
        pass  # Server not found, will return empty list
    return []


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
