import os
from logging.config import fileConfig
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

project_root = Path(__file__).resolve().parents[2]
load_dotenv(project_root / ".env")

url = config.get_main_option("sqlalchemy.url")
if url:
    db_password = os.getenv("DB_PASSWORD")
    mysql_password = os.getenv("MYSQL_PASSWORD")
    if db_password:
        url = url.replace("DB_PASSWORD", quote_plus(db_password))
    if mysql_password:
        url = url.replace("MYSQL_PASSWORD", quote_plus(mysql_password))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))

target_metadata = None


def run_migrations_offline() -> None:
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
