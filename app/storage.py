"""Persistencia local de ejecuciones y casos para el MVP."""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "finia.db"


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            executed_at TEXT NOT NULL,
            summary_json TEXT NOT NULL,
            analysis_json TEXT NOT NULL,
            report_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            transaction_id TEXT,
            severity TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN',
            finding_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(run_id) REFERENCES runs(id)
        );
        """)


def save_run(report, analysis):
    now = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        cur = db.execute("INSERT INTO runs(executed_at,summary_json,analysis_json,report_json) VALUES(?,?,?,?)",
                         (now, json.dumps(report["summary"]), json.dumps(analysis), json.dumps(report)))
        run_id = cur.lastrowid
        for tx in report.get("transactions", []):
            if tx.get("status") == "MATCHED":
                continue
            db.execute("INSERT INTO cases(run_id,transaction_id,severity,status,finding_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                       (run_id, tx.get("transaction_id"), tx.get("severity", "INFO"), "OPEN", json.dumps(tx), now, now))
    return run_id


def list_cases(status=None):
    with connect() as db:
        query = "SELECT * FROM cases"
        params = ()
        if status:
            query += " WHERE status=?"
            params = (status,)
        query += " ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END, created_at DESC"
        return [dict(row) | {"finding": json.loads(row["finding_json"])} for row in db.execute(query, params)]


def update_case(case_id, status):
    now = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        cur = db.execute("UPDATE cases SET status=?, updated_at=? WHERE id=?", (status, now, case_id))
        return cur.rowcount > 0


def list_runs(limit=20):
    with connect() as db:
        rows = db.execute("SELECT id,executed_at,summary_json FROM runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [{"id": r["id"], "executed_at": r["executed_at"], "summary": json.loads(r["summary_json"])} for r in rows]


def latest_run():
    with connect() as db:
        row = db.execute("SELECT id,executed_at,report_json,analysis_json FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        if not row:
            return None
        return {"id": row["id"], "executed_at": row["executed_at"],
                "report": json.loads(row["report_json"]),
                "analysis": json.loads(row["analysis_json"])}
