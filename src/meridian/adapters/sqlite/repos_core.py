"""Repository shell for core tables (threads, messages, actions, lookups, turns) (AEA-02 shell; body: AEA-10, cases.md section 1.2)."""

from __future__ import annotations

import sqlite3


class CoreRepos:
    """core tables (threads, messages, actions, lookups, turns). Body by AEA-10; AEA-02 creates the constructor only."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
