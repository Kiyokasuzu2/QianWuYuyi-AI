import os
import json
from datetime import datetime, timedelta

from src.audit.audit_logger import AuditLogger, _TIME_FORMAT


def test_audit_log_write_and_query(tmp_path):
    audit_file = tmp_path / "audit.log"
    logger = AuditLogger(path=str(audit_file))
    # write a few entries
    now = datetime.utcnow()
    t1 = now.strftime(_TIME_FORMAT)
    logger.log(component="proposal_manager", action="create_proposal", details={"id": "p1"}, timestamp=t1)
    t2 = (now + timedelta(seconds=1)).strftime(_TIME_FORMAT)
    logger.log(component="proposal_manager", action="accept_proposal", details={"id": "p1"}, timestamp=t2)
    t3 = (now + timedelta(seconds=2)).strftime(_TIME_FORMAT)
    logger.log(component="memory_store", action="write_memory", details={"key": "k"}, timestamp=t3)

    # query component filter
    res = logger.query(component="proposal_manager", page=1, per_page=10)
    assert res["total"] == 2
    assert all(e["component"] == "proposal_manager" for e in res["entries"])

    # query time range (only t2..t3)
    start = t2
    res2 = logger.query(start_time=start, page=1, per_page=10)
    # should include t2 and t3 => at least 2 entries
    assert res2["total"] >= 2


def test_pagination(tmp_path):
    audit_file = tmp_path / "audit.log"
    logger = AuditLogger(path=str(audit_file))
    for i in range(25):
        logger.log(component="c", action=f"a{i}", details={"i": i})
    res = logger.query(component="c", page=2, per_page=10)
    assert res["page"] == 2
    assert res["per_page"] == 10
    assert len(res["entries"]) == 10
