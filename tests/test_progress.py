from backend.app.database import init_db
from backend.app.services import dashboard, save_checkpoint


def test_dashboard_and_checkpoint_progress():
    init_db()
    before = dashboard("ana")
    assert before["total_modules"] >= 1
    progress = save_checkpoint("M00", {"user_id": "ana", "checkpoint_id": "cp1", "status": "done", "evidence": "ok"})
    assert progress["completed_checkpoints"] >= 1
