from concurrent.futures import ThreadPoolExecutor
from database.repository import F1Repository

def test_null_key_upsert_is_idempotent(tmp_path):
    repo=F1Repository(tmp_path/"nulls.sqlite")
    repo.save_dataset("p","d",[1])
    repo.save_dataset("p","d",[2])
    assert repo.counts()["datasets"] == 1
    assert repo.latest_datasets()[0]["payload"] == "[2]"

def test_concurrent_upserts_are_idempotent(tmp_path):
    repo=F1Repository(tmp_path/"concurrent.sqlite")
    def save(_): repo.save_dataset("p","d",[1],season=2026,event_key="e",session_key="s")
    with ThreadPoolExecutor(max_workers=8) as pool: list(pool.map(save,range(24)))
    assert repo.counts()["datasets"] == 1

def test_distinct_sessions_remain_distinct(tmp_path):
    repo=F1Repository(tmp_path/"sessions.sqlite")
    repo.save_dataset("p","laps",[1],season=2026,session_key="race")
    repo.save_dataset("p","laps",[2],season=2026,session_key="qualifying")
    assert repo.counts()["datasets"] == 2
