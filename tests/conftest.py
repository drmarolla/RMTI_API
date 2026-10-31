"""The lock guard (registry.lock) reads docs/PREREGISTRATION_lung.md, which the platform does not ship. These registry tests lock
throwaway copies, so give them a declaration equal to the registry's own active ladder. The guard itself is tested in the repo
(rmti-python/tests/test_lock_guard.py) against the real pre-registration text."""
import pytest
import registry as R


@pytest.fixture(autouse=True)
def _prereg_declaration(monkeypatch):
    monkeypatch.setattr(R, "prereg_ladder", lambda: (R.load()["parameters"].get("active_ladder", "A"), "test-prereg-hash"))
