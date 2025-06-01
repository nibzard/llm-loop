"""Logging utilities for LLM Loop."""

import os
import pathlib
from typing import Optional

import sqlite_utils


def get_logs_db_path() -> pathlib.Path:
    """Get the logs database path."""
    home = pathlib.Path.home()
    return home / ".config" / "io.datasette.llm" / "logs.db"


def logs_enabled() -> bool:
    """Check if logging is enabled."""
    return os.environ.get("LLM_LOGS_OFF") != "1"


def setup_logging(db_path: Optional[pathlib.Path] = None) -> Optional[sqlite_utils.Database]:
    """Set up logging database.
    
    Args:
        db_path: Optional custom database path
        
    Returns:
        Database instance or None if setup failed
    """
    if not logs_enabled():
        return None
        
    try:
        resolved_path = db_path or get_logs_db_path()
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        
        db = sqlite_utils.Database(str(resolved_path))
        migrate_db(db)
        
        return db
    except Exception:
        return None


def migrate_db(db: sqlite_utils.Database) -> None:
    """Migrate database schema.
    
    Args:
        db: Database instance to migrate
    """
    try:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY,
                model TEXT,
                prompt TEXT,
                response TEXT,
                datetime_utc TEXT
            );
        """)
    except Exception:
        pass  # Ignore migration errors for now