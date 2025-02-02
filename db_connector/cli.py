import typer
from rich.console import Console
from rich.table import Table
from .credentials import set_credentials, check_credentials, get_credentials
from .db_engine import get_engine

app = typer.Typer()
console = Console()

@app.command("set-credentials")
def set_credentials_cmd(db_type: str = typer.Option(..., '-t', '--db-type', help='Database type'), user: str = typer.Option(..., '-u', '--user', help='User account')):
    """Interactively set credentials for the database."""
    if db_type.lower() == 'snowflake':
        token = typer.prompt("Enter API token", hide_input=True)
        # Store the token in keyring or wherever appropriate
        # keyring.set_password("db_connector", f"{db_type}:{user}:api_token", token)
    set_credentials(db_type, user)

@app.command("check-credentials")
def check_credentials_cmd(db_type: str = typer.Option(..., '-t', '--db-type', help='Database type'), user: str = typer.Option(..., '-u', '--user', help='User account')):
    """Check if credentials exist for the given database and display status."""
    creds = check_credentials(db_type, user)
    table = Table(title=f"Credentials for {db_type}")
    table.add_column("User", justify="left")
    table.add_column("Field Set", justify="left")

    if creds:
        table.add_row(user, "✔️")  # Check mark if set
    else:
        table.add_row(user, "❌")  # Cross if not set

    console.print(table)

@app.command("get-engine")
def get_engine_cmd(db_type: str = typer.Option(..., '-t', '--db-type', help='Database type'), user: str = typer.Option(..., '-u', '--user', help='User account'), account: str = None, host: str = None, port: int = 1521, sid: str = None):
    """Retrieve SQLAlchemy engine for the database.
    For Snowflake, provide account.
    For Oracle, provide host, port, and sid.
    """
    try:
        params = {}
        if account:
            params['account'] = account
        if host:
            params['host'] = host
        if sid:
            params['sid'] = sid
        if port:
            params['port'] = port
        engine = get_engine(db_type, user, **params)
        typer.echo(f"Engine created: {engine.url}")
    except Exception as e:
        typer.echo(f"Error: {e}")

if __name__ == "__main__":
    app()