"""Repository shell for identity and verification codes (AEA-02 shell; body: AEA-27, graph-tools section 5)."""

from __future__ import annotations

import sqlite3


class IdentityRepos:
    """identity and verification codes. Body by AEA-27; AEA-02 creates the constructor only."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
