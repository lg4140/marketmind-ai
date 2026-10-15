"""Persist opt-in user feedback against an existing run only."""
from __future__ import annotations
from pathlib import Path
from agents.run_store import RunStore

def save_feedback(db_path: str | Path, run_id: str, rating: int, comment: str='') -> None:
    RunStore(db_path).feedback(run_id, rating, comment)
