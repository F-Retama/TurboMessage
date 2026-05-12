"""Minimal persistence and business rules for TurboMessage."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any

MAX_INBOX = 5
MAX_OUTBOX = 5

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "grpc_server" / "data" / "turbomessage.db"

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id TEXT NOT NULL,
    recipient_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0 CHECK (is_read IN (0, 1)),
    sender_deleted INTEGER NOT NULL DEFAULT 0 CHECK (sender_deleted IN (0, 1)),
    recipient_deleted INTEGER NOT NULL DEFAULT 0 CHECK (recipient_deleted IN (0, 1)),
    FOREIGN KEY (sender_id) REFERENCES users (id),
    FOREIGN KEY (recipient_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender_id);
CREATE INDEX IF NOT EXISTS idx_emails_recipient ON emails(recipient_id);
"""


class Storage:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = threading.RLock()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, isolation_level=None, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(SCHEMA_SQL)

    def register(self, username: str, password: str) -> tuple[bool, str, str]:
        username = username.strip()
        password = password.strip()
        if not username or not password:
            return False, "username and password are required", ""

        with self._write_lock:
            conn = self._conn()
            try:
                conn.execute("BEGIN IMMEDIATE")
                user_id = f"{username}@turbo.com"
                conn.execute(
                    """
                    INSERT INTO users(id, username, password)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, username, password),
                )
                conn.commit()
                return True, "user created", user_id
            except sqlite3.IntegrityError:
                conn.rollback()
                return False, "username already exists", ""
            except sqlite3.Error:
                conn.rollback()
                return False, "database error", ""
            finally:
                conn.close()

    def login(self, username: str, password: str) -> tuple[bool, str, str]:
        username = username.strip()
        password = password.strip()
        if not username or not password:
            return False, "username and password are required", ""

        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, password FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        if not row or row["password"] != password:
            return False, "invalid credentials", ""
        return True, "login ok", str(row["id"])

    def send_email(
        self, sender_id: str, recipient_id: str, subject: str, body: str
    ) -> tuple[bool, str, int]:
        sender_id = sender_id.strip()
        recipient_id = recipient_id.strip()
        if not sender_id or not recipient_id:
            return False, "sender_id and recipient_id are required", 0

        with self._write_lock:
            conn = self._conn()
            try:
                conn.execute("BEGIN IMMEDIATE")
                if not self._user_exists(conn, sender_id):
                    conn.rollback()
                    return False, "sender does not exist", 0
                if not self._user_exists(conn, recipient_id):
                    conn.rollback()
                    return False, "recipient does not exist", 0

                outbox_count = self._count_outbox(conn, sender_id)
                if outbox_count >= MAX_OUTBOX:
                    conn.rollback()
                    return False, "sender outbox is full", 0

                inbox_count = self._count_inbox(conn, recipient_id)
                if inbox_count >= MAX_INBOX:
                    conn.rollback()
                    return False, "recipient inbox is full", 0

                cursor = conn.execute(
                    """
                    INSERT INTO emails(
                        sender_id, recipient_id, subject, body, is_read,
                        sender_deleted, recipient_deleted
                    )
                    VALUES (?, ?, ?, ?, 0, 0, 0)
                    """,
                    (sender_id, recipient_id, subject, body),
                )
                email_id = int(cursor.lastrowid)
                conn.commit()
                return True, "email sent", email_id
            except sqlite3.Error:
                conn.rollback()
                return False, "database error", 0
            finally:
                conn.close()

    def list_emails(self, user_id: str) -> tuple[bool, str, list[dict[str, Any]]]:
        user_id = user_id.strip()
        if not user_id:
            return False, "user_id is required", []

        with self._conn() as conn:
            if not self._user_exists(conn, user_id):
                return False, "user does not exist", []
            rows = conn.execute(
                """
                     SELECT id, sender_id, recipient_id, subject, body, is_read
                FROM emails
                WHERE (sender_id = ? AND sender_deleted = 0)
                   OR (recipient_id = ? AND recipient_deleted = 0)
                     ORDER BY id DESC
                """,
                (user_id, user_id),
            ).fetchall()
        return True, "emails listed", [dict(row) for row in rows]

    def read_email(self, user_id: str, email_id: int) -> tuple[bool, str, dict[str, Any] | None]:
        user_id = user_id.strip()
        if not user_id:
            return False, "user_id is required", None

        with self._write_lock:
            conn = self._conn()
            try:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute(
                    """
                    SELECT id, sender_id, recipient_id, subject, body, is_read,
                              sender_deleted, recipient_deleted
                    FROM emails
                    WHERE id = ?
                    """,
                    (email_id,),
                ).fetchone()
                if not row:
                    conn.rollback()
                    return False, "email not found", None

                if not self._can_access_email(row, user_id):
                    conn.rollback()
                    return False, "email not accessible by this user", None

                if row["recipient_id"] == user_id and row["is_read"] == 0:
                    conn.execute("UPDATE emails SET is_read = 1 WHERE id = ?", (email_id,))

                result_row = conn.execute(
                    """
                    SELECT id, sender_id, recipient_id, subject, body, is_read
                    FROM emails
                    WHERE id = ?
                    """,
                    (email_id,),
                ).fetchone()
                conn.commit()
                return True, "email read", dict(result_row)
            except sqlite3.Error:
                conn.rollback()
                return False, "database error", None
            finally:
                conn.close()

    def delete_email(self, user_id: str, email_id: int) -> tuple[bool, str]:
        user_id = user_id.strip()
        if not user_id:
            return False, "user_id is required"

        with self._write_lock:
            conn = self._conn()
            try:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute(
                    """
                    SELECT id, sender_id, recipient_id, sender_deleted, recipient_deleted
                    FROM emails
                    WHERE id = ?
                    """,
                    (email_id,),
                ).fetchone()
                if not row:
                    conn.rollback()
                    return False, "email not found"

                sender_deleted = int(row["sender_deleted"])
                recipient_deleted = int(row["recipient_deleted"])

                touched = False
                if row["sender_id"] == user_id and sender_deleted == 0:
                    sender_deleted = 1
                    touched = True
                if row["recipient_id"] == user_id and recipient_deleted == 0:
                    recipient_deleted = 1
                    touched = True

                if not touched:
                    conn.rollback()
                    return False, "email not accessible by this user"

                conn.execute(
                    """
                    UPDATE emails
                    SET sender_deleted = ?, recipient_deleted = ?
                    WHERE id = ?
                    """,
                    (sender_deleted, recipient_deleted, email_id),
                )

                if sender_deleted == 1 and recipient_deleted == 1:
                    conn.execute("DELETE FROM emails WHERE id = ?", (email_id,))

                conn.commit()
                return True, "email deleted"
            except sqlite3.Error:
                conn.rollback()
                return False, "database error"
            finally:
                conn.close()

    @staticmethod
    def _user_exists(conn: sqlite3.Connection, user_id: str) -> bool:
        row = conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone()
        return row is not None

    @staticmethod
    def _count_outbox(conn: sqlite3.Connection, user_id: str) -> int:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM emails WHERE sender_id = ? AND sender_deleted = 0",
            (user_id,),
        ).fetchone()
        return int(row["total"])

    @staticmethod
    def _count_inbox(conn: sqlite3.Connection, user_id: str) -> int:
        row = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM emails
            WHERE recipient_id = ? AND recipient_deleted = 0
            """,
            (user_id,),
        ).fetchone()
        return int(row["total"])

    @staticmethod
    def _can_access_email(row: sqlite3.Row, user_id: str) -> bool:
        can_access_as_sender = row["sender_id"] == user_id and int(row["sender_deleted"]) == 0
        can_access_as_recipient = (
            row["recipient_id"] == user_id and int(row["recipient_deleted"]) == 0
        )
        return can_access_as_sender or can_access_as_recipient
