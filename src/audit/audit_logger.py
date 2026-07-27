from __future__ import annotations
import json
import os
import threading
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from src.contracts.audit_schema import AuditEntry

DEFAULT_AUDIT_FILE = os.path.join("data", "audit.log")
_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _now_iso() -> str:
    return datetime.utcnow().strftime(_TIME_FORMAT)


class AuditLogger:
    def __init__(self, path: str = DEFAULT_AUDIT_FILE):
        self.path = path
        self._lock = threading.Lock()
        # ensure dir exists
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        # create file if not exists
        if not os.path.exists(self.path):
            open(self.path, "a", encoding="utf-8").close()

    def log(self, component: str, action: str, details: Optional[Dict[str, Any]] = None, level: str = "info", timestamp: Optional[str] = None) -> None:
        """
        Append a JSONL audit entry.
        fields: timestamp (ISO UTC), component, action, details, level
        """
        entry = {
            "timestamp": timestamp or _now_iso(),
            "component": component,
            "action": action,
            "level": level,
            "details": details or {}
        }
        line = json.dumps(entry, ensure_ascii=False)
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def _iter_entries(self) -> Iterable[AuditEntry]:
        with open(self.path, "r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    yield json.loads(raw)
                except json.JSONDecodeError:
                    # skip malformed lines but could be logged
                    continue

    def query(self, component: Optional[str] = None, action: Optional[str] = None,
              start_time: Optional[str] = None, end_time: Optional[str] = None,
              page: int = 1, per_page: int = 100) -> Dict[str, Any]:
        """
        Simple query over JSONL:
         - component, action filters (exact match)
         - start_time / end_time ISO (inclusive)
         - pagination by page/per_page (1-indexed)
        Returns: { total: int, page: int, per_page: int, entries: [ ... ] }
        """
        # parse times
        def _parse(t: Optional[str]) -> Optional[datetime]:
            if t is None:
                return None
            try:
                return datetime.strptime(t, _TIME_FORMAT)
            except Exception:
                # try without microseconds
                try:
                    return datetime.fromisoformat(t.replace("Z", "+00:00")).replace(tzinfo=None)
                except Exception:
                    return None

        start_dt = _parse(start_time)
        end_dt = _parse(end_time)

        matched: List[AuditEntry] = []
        for entry in self._iter_entries():
            if component and entry.get("component") != component:
                continue
            if action and entry.get("action") != action:
                continue
            ts_str = entry.get("timestamp")
            if ts_str:
                try:
                    ts = datetime.strptime(ts_str, _TIME_FORMAT)
                except Exception:
                    # fallback parse
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    except Exception:
                        ts = None
            else:
                ts = None
            if start_dt and ts and ts < start_dt:
                continue
            if end_dt and ts and ts > end_dt:
                continue
            matched.append(entry)

        total = len(matched)
        # simple pagination
        if per_page <= 0:
            per_page = 100
        page = max(1, page)
        start = (page - 1) * per_page
        end = start + per_page
        page_entries = matched[start:end]
        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "entries": page_entries
        }
