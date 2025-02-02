# db-connector

A command-line tool to manage database connection settings using Typer, keyring, and SQLAlchemy.

## Features
- **Interactive Credential Management:** Set and check database credentials interactively.
- **Multiple Database Support:** Currently supports Snowflake and Oracle.
- **Secure Storage:** Credentials are stored using keyring; falls back to environment variables if not set.
- **SQLAlchemy Integration:** Provides an API to retrieve a SQLAlchemy engine based on stored credentials.

## Installation

Use the provided installation scripts or install via pip:

### Linux
```
bash install_linux.sh
```

### Windows
```
bat install_windows.bat
```

Alternatively, install directly:

```
pip install .
```

## Usage

After installation, use the `db-connector` command:

- Set credentials:
```
db-connector set-credentials <db_type> <user>
```

- Check credentials:
```
db-connector check-credentials <db_type> <user>
```

- Get SQLAlchemy engine:
```
db-connector get-engine <db_type> <user> [--account ACCOUNT] [--host HOST] [--port PORT] [--sid SID]
```

## Development

Use the Makefile for common tasks:

- **install:** Install the package in editable mode.
- **test:** Run the test suite.
- **build:** Build the package.
- **clean:** Remove build artifacts.

## License

MIT License
