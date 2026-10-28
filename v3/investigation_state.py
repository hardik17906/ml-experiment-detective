"""Local workflow state, proposal revisions and atomic execution permissions."""

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "investigations" / "investigations.sqlite3"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def event(state, kind, data, origin="PYTHON"):
    state.setdefault("trace", []).append({"kind": kind, "origin": origin, "data": data})


class InvestigationStore:
    def __init__(self, path=DEFAULT_DB):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS investigations
                (id TEXT PRIMARY KEY, objective TEXT, status TEXT, updated TEXT, state TEXT);
                CREATE TABLE IF NOT EXISTS proposals
                (id TEXT PRIMARY KEY, investigation_id TEXT, hash TEXT, payload TEXT,
                 status TEXT, mode TEXT, execution TEXT);
                CREATE TABLE IF NOT EXISTS decisions
                (id INTEGER PRIMARY KEY, proposal_id TEXT, hash TEXT, decision TEXT,
                 mode TEXT, actor TEXT, reason TEXT, timestamp TEXT);
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def create(self, objective, model_enabled=True):
        identifier = "INV-" + uuid.uuid4().hex[:10].upper()
        state = {"investigation_id": identifier, "objective": objective,
                 "status": "created", "model_enabled": model_enabled,
                 "plan": [], "trace": [], "evidence": {}, "hypotheses": [],
                 "uncertainties": [], "proposal_id": None, "report": ""}
        self.save(state)
        return state

    def save(self, state):
        with self.connection() as db:
            db.execute("INSERT OR REPLACE INTO investigations VALUES (?,?,?,?,?)",
                       (state["investigation_id"], state["objective"], state["status"],
                        now(), json.dumps(state, allow_nan=False)))

    def load(self, identifier):
        with self.connection() as db:
            row = db.execute("SELECT state FROM investigations WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown investigation: {identifier}")
        return json.loads(row[0])

    def list(self, *, research_only=False):
        with self.connection() as db:
            rows = db.execute("SELECT id,objective,status,updated,state FROM investigations ORDER BY updated DESC").fetchall()
        return [{k:row[k] for k in ("id","objective","status","updated")} for row in rows
                if not research_only or json.loads(row["state"]).get("plan")]

    def put_proposal(self, identifier, proposal):
        hashed = digest(proposal)
        with self.connection() as db:
            old = db.execute("SELECT * FROM proposals WHERE id=?", (proposal["proposal_id"],)).fetchone()
            if old and old["investigation_id"] != identifier:
                raise ValueError("Proposal belongs to another investigation")
            if old and old["hash"] == hashed:
                return hashed  # Idempotent node replay must not erase an existing decision.
            if old and old["status"] in {"running", "completed", "dry_run_completed"}:
                raise ValueError("Create a new investigation to replace an executed proposal")
            db.execute("INSERT OR REPLACE INTO proposals VALUES (?,?,?,?,?,?,?)",
                       (proposal["proposal_id"], identifier, hashed, json.dumps(proposal), "pending", None, None))
            if old:
                db.execute("INSERT INTO decisions VALUES (NULL,?,?,?,?,?,?,?)",
                           (proposal["proposal_id"], hashed, "modified", "none", "user",
                            "Configuration changed; previous approval invalidated", now()))
        return hashed

    def proposal(self, proposal_id):
        with self.connection() as db:
            row = db.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown proposal")
        result = dict(row)
        result["payload"] = json.loads(result["payload"])
        result["execution"] = json.loads(result["execution"]) if result["execution"] else None
        return result

    def decide(self, proposal_id, expected_hash, decision, mode="dry_run", reason="", actor="user"):
        if decision not in {"approved", "rejected", "deferred"} or mode not in {"dry_run", "live"}:
            raise ValueError("Invalid decision or execution mode")
        if actor not in {"user", "development_dry_run"} or (actor == "development_dry_run" and mode != "dry_run"):
            raise PermissionError("Only the user can approve live training")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
            if not row or row["hash"] != expected_hash:
                raise PermissionError("Stale proposal: inspect the exact current configuration again")
            if row["status"] in {"running", "completed", "dry_run_completed"}:
                raise PermissionError("This permission has already been consumed")
            db.execute("UPDATE proposals SET status=?,mode=? WHERE id=?", (decision, mode, proposal_id))
            db.execute("INSERT INTO decisions VALUES (NULL,?,?,?,?,?,?,?)",
                       (proposal_id, expected_hash, decision, mode, actor, reason, now()))

    def decisions(self, proposal_id):
        with self.connection() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM decisions WHERE proposal_id=? ORDER BY id", (proposal_id,))]

    def claim_execution(self, proposal_id, expected_hash, mode):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
            if not row or row["hash"] != expected_hash or row["status"] != "approved" or row["mode"] != mode:
                raise PermissionError("Execution requires unused approval for this exact proposal hash and mode")
            if mode == "live" and db.execute("SELECT id FROM proposals WHERE status='running' AND mode='live' AND id<>?", (proposal_id,)).fetchone():
                raise PermissionError("Another live experiment is already active; inspect it before starting another")
            db.execute("UPDATE proposals SET status='running' WHERE id=?", (proposal_id,))

    def execution_result(self, proposal_id, result):
        with self.connection() as db:
            db.execute("UPDATE proposals SET status=?,execution=? WHERE id=?",
                       (result["status"], json.dumps(result), proposal_id))
