#!/usr/bin/env python3
import os
import subprocess
import click
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.sql import SqlManagementClient
from dotenv import load_dotenv, set_key

load_dotenv()

def get_credential():
    """Gets the Azure credential."""
    return DefaultAzureCredential()

def get_subscription_client():
    """Gets the subscription client."""
    return SubscriptionClient(get_credential())

def get_sql_client(subscription_id):
    """Gets the SQL management client."""
    return SqlManagementClient(get_credential(), subscription_id)

@click.group()
def cli():
    """A utility for managing Azure SQL databases."""
    pass

@cli.command()
def login():
    """Authenticates the user with Azure and lists subscriptions."""
    try:
        subscription_client = get_subscription_client()
        subscriptions = list(subscription_client.subscriptions.list())
        
        if not subscriptions:
            click.echo("No subscriptions found. Please ensure you have access to at least one subscription.")
            return

        click.echo("Authentication successful. Available subscriptions:")
        for sub in subscriptions:
            click.echo(f"- {sub.display_name} ({sub.subscription_id})")
            
    except Exception as e:
        click.echo(f"Authentication failed: {e}")

@cli.command()
@click.option('--subscription-id', help='The ID of the subscription to use.')
def select_subscription(subscription_id):
    """Selects an Azure subscription to use."""
    if not subscription_id:
        subscription_client = get_subscription_client()
        subscriptions = list(subscription_client.subscriptions.list())
        for i, sub in enumerate(subscriptions):
            click.echo(f"{i+1}. {sub.display_name} ({sub.subscription_id})")
        sub_index = click.prompt('Please enter the number of the subscription to use', type=int)
        subscription_id = subscriptions[sub_index-1].subscription_id
    
    set_key('.env', 'AZURE_SUBSCRIPTION_ID', subscription_id)
    click.echo(f"Selected subscription: {subscription_id}")

@cli.command()
def list_servers():
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
@click.option('--server-name', prompt='Server Name', help='The name of the SQL server.')
def list_databases(server_name):
    """Lists databases on a SQL server."""
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    if not subscription_id:
        click.echo("Please select a subscription first using 'select-subscription'.")
        return
        
    sql_client = get_sql_client(subscription_id)
    # Need to get resource group name
    # This is a simplification, assuming the server is in the first resource group found
    resource_groups = list(get_subscription_client().resource_groups.list())
    if not resource_groups:
        click.echo("No resource groups found in the subscription.")
        return
    resource_group_name = resource_groups[0].name
    
    databases = list(sql_client.databases.list_by_server(resource_group_name, server_name))
    
    if not databases:
        click.echo("No databases found on the specified server.")
        return
        
    click.echo("Available databases:")
    for db in databases:
        click.echo(f"- {db.name}")

@cli.command()
@click.option('--server-name', prompt='Server Name', help='The name of the SQL server.')
@click.option('--database-name', prompt='Database Name', help='The name of the database.')
@click.option('--output-file', default='database.bacpac', help='The output file for the bacpac.')
def extract_bacpac(server_name, database_name, output_file):
    """Extracts a bacpac from an Azure SQL database."""
    click.echo(f"Extracting bacpac from {database_name} on {server_name}...")
    # This requires sqlpackage to be installed and in the PATH
    # You will also need to be authenticated with Azure AD
    command = [
        'sqlpackage',
        '/Action:Export',
        f'/SourceServerName:{server_name}.database.windows.net',
        f'/SourceDatabaseName:{database_name}',
        f'/TargetFile:{output_file}',
        '/p:Storage=Memory',
        '/p:Authentication=ActiveDirectoryInteractive'
    ]
    try:
        subprocess.run(command, check=True)
        click.echo(f"Successfully extracted bacpac to {output_file}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        click.echo(f"Error extracting bacpac: {e}")
        click.echo("Please ensure 'sqlpackage' is installed and in your PATH.")

@cli.command()
@click.option('--input-file', prompt='Input File', help='The bacpac file to import.')
@click.option('--server-name', default='localhost', help='The name of the local SQL server.')
@click.option('--database-name', prompt='Database Name', help='The name of the target database.')
def import_bacpac(input_file, server_name, database_name):
    """Imports a bacpac to a local SQL server."""
    click.echo(f"Importing {input_file} to {database_name} on {server_name}...")
    command = [
        'sqlpackage',
        '/Action:Import',
        f'/SourceFile:{input_file}',
        f'/TargetServerName:{server_name}',
        f'/TargetDatabaseName:{database_name}',
    ]
    try:
        subprocess.run(command, check=True)
        click.echo(f"Successfully imported {input_file} to {database_name}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        click.echo(f"Error importing bacpac: {e}")
        click.echo("Please ensure 'sqlpackage' is installed and in your PATH.")

if __name__ == '__main__':
    cli()
