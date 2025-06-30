import os
import sys
from logging.config import fileConfig
from configparser import ConfigParser

from alembic import context
from alembic.config import Config
from sqlalchemy import engine_from_config, pool

# ─────────────────────────────────────────────────────────────────────────────
# 1) Make sure your app’s parent dir is on the path so models import cleanly
# ─────────────────────────────────────────────────────────────────────────────
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─────────────────────────────────────────────────────────────────────────────
# 2) Disable %-interpolation (so %04d lines in alembic.ini won’t blow up)
# ─────────────────────────────────────────────────────────────────────────────
alembic_cfg = Config()
# attach a parser with no interpolation
alembic_cfg.parser = ConfigParser(interpolation=None)
alembic_cfg.config_file_name = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "alembic.ini"
)

# ─────────────────────────────────────────────────────────────────────────────
# 3) Set up logging from the .ini (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
if alembic_cfg.config_file_name is not None:
    fileConfig(alembic_cfg.config_file_name)

# ─────────────────────────────────────────────────────────────────────────────
# 4) Import your MetaData so Alembic can “see” all models
# ─────────────────────────────────────────────────────────────────────────────
from models import User, Event, EventRegistration, Photo  # noqa: E402
from database.connection import Base                         # noqa: E402
target_metadata = Base.metadata

# ─────────────────────────────────────────────────────────────────────────────
# 5) Override the URL with the one Render provides at runtime
# ─────────────────────────────────────────────────────────────────────────────
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL env var not set—did you wire it in render.yaml?")
alembic_cfg.set_main_option("sqlalchemy.url", database_url)

# ─────────────────────────────────────────────────────────────────────────────
# 6) Migration routines (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    url = alembic_cfg.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata,
        literal_binds=True, dialect_opts={"paramstyle": "named"}
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        alembic_cfg.get_section(alembic_cfg.config_ini_section),
        prefix="sqlalchemy.", poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
