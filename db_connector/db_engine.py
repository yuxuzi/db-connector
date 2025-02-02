import os
from abc import ABC, abstractmethod
from sqlalchemy import create_engine
from .credentials import get_credentials


class BaseEngineBuilder(ABC):
    @abstractmethod
    def build_engine(self, user: str, password: str, **kwargs):
        pass


class SnowflakeEngineBuilder(BaseEngineBuilder):
    def build_engine(self, user: str, password: str, **kwargs):
        account = kwargs.get('account') or os.environ.get('SNOWFLAKE_ACCOUNT')
        if not account:
            raise ValueError("Snowflake account identifier must be provided via argument or SNOWFLAKE_ACCOUNT environment variable")
        # Construct URI: snowflake://<user>:<password>@<account>
        uri = f"snowflake://{user}:{password}@{account}"
        return create_engine(uri)


class OracleEngineBuilder(BaseEngineBuilder):
    def build_engine(self, user: str, password: str, **kwargs):
        host = kwargs.get('host') or os.environ.get('ORACLE_HOST')
        port = kwargs.get('port') or os.environ.get('ORACLE_PORT', 1521)
        sid = kwargs.get('sid') or os.environ.get('ORACLE_SID')
        if not host or not sid:
            raise ValueError("Oracle host and SID must be provided via arguments or environment variables (ORACLE_HOST, ORACLE_SID)")
        # Construct URI: oracle://<user>:<password>@<host>:<port>/<sid>
        uri = f"oracle://{user}:{password}@{host}:{port}/{sid}"
        return create_engine(uri)


# Registry of engine builders
engine_builders = {
    'snowflake': SnowflakeEngineBuilder(),
    'oracle': OracleEngineBuilder(),
}


def get_engine(db_type: str, user: str, **kwargs):
    """
    Retrieve a SQLAlchemy engine for a given db_type and user using dependency injection.
    The appropriate engine builder (e.g. SnowflakeEngineBuilder or OracleEngineBuilder) is selected from the registry.
    """
    creds = get_credentials(db_type, user)
    if not creds or 'password' not in creds:
        raise ValueError(f"Credentials not found for {db_type} user {user}")

    password = creds['password']
    builder = engine_builders.get(db_type.lower())
    if not builder:
        raise ValueError(f"Unsupported database type: {db_type}")

    engine = builder.build_engine(user, password, **kwargs)
    return engine


def create_connection_string(db_type: str, user: str, **kwargs):
    """
    Create a connection string for the specified database type and user.
    This can be used in other applications.
    """
    creds = get_credentials(db_type, user)
    if not creds or 'password' not in creds:
        raise ValueError(f"Credentials not found for {db_type} user {user}")

    password = creds['password']
    builder = engine_builders.get(db_type.lower())
    if not builder:
        raise ValueError(f"Unsupported database type: {db_type}")

    # Construct the connection string using the builder
    connection_string = builder.build_engine(user, password, **kwargs).url
    return connection_string
