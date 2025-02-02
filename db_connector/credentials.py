import os
import keyring
import typer

def set_credentials(db_type: str, user: str):
    """
    Interactively set credentials for a given database type and user,
    then store them securely using keyring.
    """
    password = typer.prompt("Enter password", hide_input=True)
    # Store the password in keyring with a composite key
    keyring_key = f"{db_type}:{user}"
    keyring.set_password("db_connector", keyring_key, password)
    typer.echo("Credentials saved.")


def get_credentials(db_type: str, user: str):
    """
    Retrieve credentials from keyring or fallback to environment variables.
    """
    keyring_key = f"{db_type}:{user}"
    password = keyring.get_password("db_connector", keyring_key)
    if password:
        return {"password": password}
    # Fallback to environment variable e.g. SNOWFLAKE_USER_PASSWORD
    env_var = f"{db_type.upper()}_{user.upper()}_PASSWORD"
    password = os.environ.get(env_var)
    if password:
        return {"password": password}
    return None


def check_credentials(db_type: str, user: str):
    """
    Check if credentials exist for the given database type and user.
    """
    creds = get_credentials(db_type, user)
    if creds:
        typer.echo("Credentials found.")
    else:
        typer.echo("Credentials not found.")



