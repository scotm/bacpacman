import questionary
from azure.core.exceptions import ClientAuthenticationError, ServiceRequestError
from dotenv import set_key
from questionary import Choice

from . import azure_handler, sql_handler
from .config import custom_style


def run_interactive_workflow() -> None:
    """Runs the full end-to-end interactive workflow."""
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
        subscriptions = azure_handler.list_subscriptions()

        # 3. Select Subscription
        subscription_choices = [
            Choice(
                title=f"{s.display_name or 'Unnamed'} ({s.subscription_id or 'No ID'})",
                value=s.subscription_id,
            )
            for s in subscriptions
            if s.subscription_id
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
        servers = list(azure_handler.list_servers(subscription_id))
        if not servers:
            questionary.print(
                "No SQL servers found in the selected subscription.",
                style="bold fg:yellow",
            )
            return

        server_choices = [Choice(s.name, s) for s in servers]
        selected_server = questionary.select(
            "Select the SQL server:", choices=server_choices, style=custom_style
        ).ask()
        if not selected_server or not selected_server.name:
            return
        selected_server_name = selected_server.name

        # 5. List and Select Database
        questionary.print("Fetching databases...", style="bold")
        if selected_server_name:
            databases = list(
                azure_handler.list_databases(subscription_id, selected_server_name)
            )
            if not databases:
                questionary.print(
                    "No databases found on the specified server.",
                    style="bold fg:yellow",
                )
                return

            db_choices = [Choice(db.name, db.name) for db in databases]
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
            sql_handler.extract_bacpac(
                selected_server_name,
                selected_database_name,
                output_file,
                auth_method_choice,
                username,
            )
        else:
            questionary.print("Extraction cancelled.", style="bold fg:red")
