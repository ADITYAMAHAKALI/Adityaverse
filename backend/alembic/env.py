from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os, sys, pathlib


ROOT_DIR = pathlib.Path(__file__).resolve().parents[2]  
sys.path.insert(0, str(ROOT_DIR))

from backend.core.config import settings          
from backend.db.session import Base            

# ── Alembic Config obj ────────────────────────────────────────────────
config = context.config
fileConfig(config.config_file_name)

# Inject runtime DB URL
config.set_main_option("sqlalchemy.url", str(settings.database_url))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
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
            compare_type=True,      # detect column type changes
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
