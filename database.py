import sqlite3
from contextlib import closing

from flask import g

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT ''
);
"""


def get_db(database_path):
    if "db" not in g:
        g.db = sqlite3.connect(database_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def init_db(database_path):
    with closing(sqlite3.connect(database_path)) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.executescript(SCHEMA)
        db.commit()
