import sqlite3
from contextlib import closing
from pathlib import Path

DB_PATH = Path("projects.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_connection()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                client_name TEXT NOT NULL,
                owner TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('New', 'In Progress', 'On Hold', 'Completed', 'Cancelled')),
                priority TEXT NOT NULL CHECK (priority IN ('Low', 'Medium', 'High', 'Urgent')),
                intake_date TEXT NOT NULL,
                due_date TEXT,
                budget REAL,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS trg_projects_updated_at
            AFTER UPDATE ON projects
            FOR EACH ROW
            BEGIN
                UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
            """
        )
        conn.commit()


def add_project(project: dict) -> None:
    with closing(get_connection()) as conn:
        conn.execute(
            """
            INSERT INTO projects (
                project_name, client_name, owner, status, priority,
                intake_date, due_date, budget, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project["project_name"],
                project["client_name"],
                project["owner"],
                project["status"],
                project["priority"],
                project["intake_date"],
                project["due_date"],
                project["budget"],
                project["notes"],
            ),
        )
        conn.commit()


def list_projects(
    search: str = "",
    status: str | None = None,
    priority: str | None = None,
) -> list[sqlite3.Row]:
    query = "SELECT * FROM projects WHERE 1=1"
    params: list = []

    if search:
        query += " AND (project_name LIKE ? OR client_name LIKE ? OR owner LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    if status and status != "All":
        query += " AND status = ?"
        params.append(status)

    if priority and priority != "All":
        query += " AND priority = ?"
        params.append(priority)

    query += " ORDER BY intake_date DESC, id DESC"

    with closing(get_connection()) as conn:
        return list(conn.execute(query, params).fetchall())


def get_project(project_id: int) -> sqlite3.Row | None:
    with closing(get_connection()) as conn:
        return conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()


def update_project(project_id: int, project: dict) -> None:
    with closing(get_connection()) as conn:
        conn.execute(
            """
            UPDATE projects
            SET project_name = ?,
                client_name = ?,
                owner = ?,
                status = ?,
                priority = ?,
                intake_date = ?,
                due_date = ?,
                budget = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                project["project_name"],
                project["client_name"],
                project["owner"],
                project["status"],
                project["priority"],
                project["intake_date"],
                project["due_date"],
                project["budget"],
                project["notes"],
                project_id,
            ),
        )
        conn.commit()


def delete_project(project_id: int) -> None:
    with closing(get_connection()) as conn:
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
