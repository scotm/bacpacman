import sys

from .azure_handler import check_azure_cli
from .cli import cli
from .sql_handler import check_sqlpackage
from .ui import run_interactive_workflow


def main() -> None:
    """The main entry point for the application."""
    check_sqlpackage()
    check_azure_cli()
    if len(sys.argv) == 1:
        run_interactive_workflow()
    else:
        cli()


if __name__ == "__main__":
    main()
