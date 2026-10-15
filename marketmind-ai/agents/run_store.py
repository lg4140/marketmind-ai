"""Local metadata-only run and step store. Does not persist raw data or model prompts."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import json
import hashlib

SCHEMA = '''
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY, mode TEXT NOT NULL, status TEXT NOT NULL,
    dataset_id TEXT NOT NULL, scope_json TEXT NOT NULL,
    created_at TEXT NOT NULL, finished_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS steps (
    run_id TEXT NOT NULL, seq INTEGER NOT NULL, tool TEXT NOT NULL,
    status TEXT NOT NULL, elapsed_ms REAL NOT NULL,
    error_code TEXT, PRIMARY KEY(run_id, seq),
    FOREIGN KEY(run_id) REFERENCES runs(run_id)
);
CREATE TABLE IF NOT EXISTS feedback (
    run_id TEXT NOT NULL, rating INTEGER NOT NULL,
    comment TEXT NOT NULL, created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(run_id)
 );
CREATE TABLE IF NOT EXISTS run_details (
    run_id TEXT PRIMARY KEY, planner_version TEXT,
    task_contract_json TEXT, model_id TEXT,
    artifact_manifest_json TEXT, 
    FOREIGN KEY(run_id) REFERENCES runs(run_id)
);'''

class RunStore:
    def __init__(self, path: str | Path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def _connect(self):
        conn=sqlite3.connect(self.path)
        conn.execute('PRAGMA foreign_keys=ON')
        return conn

    def record(self, result, dataset_id: str, model_id: str | None = None):
        now=datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)',
               (result.run_id, result.mode, result.status, dataset_id,
                json.dumps(result.scope, ensure_ascii=False), now, now))
            contract=getattr(result,'task_contract',None)
            manifest=[]
            for path_str in result.report.artifact_paths:
                artifact=Path(path_str)
                manifest.append({'path':str(artifact),
                    'sha256':hashlib.sha256(artifact.read_bytes()).hexdigest() if artifact.is_file() else None})
            conn.execute('INSERT INTO run_details VALUES (?,?,?,?,?)',(
                result.run_id,contract.planner_version if contract else None,
                contract.model_dump_json() if contract else None,model_id,
                json.dumps(manifest,ensure_ascii=False)))
            for i, step in enumerate(result.trace):
                conn.execute('INSERT INTO steps VALUES (?,?,?,?,?,?)',
                   (result.run_id,i,step['tool'],step['status'],float(step['elapsed_ms']),step.get('error_code')))

    def details(self,run_id:str):
        with self._connect() as conn:
            row=conn.execute('SELECT planner_version,task_contract_json,model_id,artifact_manifest_json FROM run_details WHERE run_id=?',(run_id,)).fetchone()
        if row is None:return None
        return {'planner_version':row[0],'task_contract':json.loads(row[1]) if row[1] else None,
                'model_id':row[2], 'artifact_manifest':json.loads(row[3])}

    def feedback(self, run_id: str, rating: int, comment: str=''):
        if rating not in (1,2,3,4,5): raise ValueError('rating must be 1 to 5')
        if len(comment)>1000: raise ValueError('comment too long')
        with self._connect() as conn:
            exists=conn.execute('SELECT 1 FROM runs WHERE run_id=?',(run_id,)).fetchone()
            if not exists: raise ValueError('Unknown run_id; cannot attach orphan feedback')
            conn.execute('INSERT INTO feedback VALUES (?,?,?,?)',
                (run_id,rating,comment,datetime.now(timezone.utc).isoformat()))

    def history(self, limit: int=20):
        with self._connect() as conn:
            rows=conn.execute('''SELECT r.run_id,r.mode,r.status,r.created_at,
                       (SELECT COUNT(*) FROM steps s WHERE s.run_id=r.run_id) AS n_steps,
                       (SELECT AVG(f.rating) FROM feedback f WHERE f.run_id=r.run_id) AS rating
                       FROM runs r ORDER BY r.created_at DESC LIMIT ?''',(limit,)).fetchall()
        return [dict(zip(['run_id','mode','status','created_at','steps','rating'], row)) for row in rows]
