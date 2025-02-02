from setuptools import setup, find_packages

setup(
    name="db-connector",
    version="0.1.0",
    author="leoliu",
    author_email="your.email@example.com",
    description="A command-line tool to manage database connection settings using Typer, keyring, and SQLAlchemy",
    packages=find_packages(),
    install_requires=[
        "typer>=0.7",
        "keyring",
        "SQLAlchemy"
    ],
    entry_points={
        "console_scripts": [
            "db-connector=db_connector.cli:app"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
