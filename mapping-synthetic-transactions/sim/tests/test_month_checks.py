"""The month's evidence checks (sim/evidence/month.py) on the 12-day carried fixture: every month target is measured."""
import csv
import os
import sys

from conftest import SIM_DIR

sys.path.insert(0, os.path.join(SIM_DIR, "evidence"))
import month  # noqa: E402


def test_every_month_target_is_measured(carried10, tmp_path):
    M = month.measure(carried10["out"])
    with open(month.TARGETS, newline="", encoding="utf-8") as f:
        targets = list(csv.DictReader(f))
    assert len(targets) == 15
    for t in targets:
        v = M["V"].get(t["metric"])
        if t["metric"] in ("snap_left_day14", "snap_left_day28"):     # need 14 and 28 days after a load; the fixture has 12
            continue
        assert v is not None, t["metric"]
        assert month.verdict(t, v) in ("in range", "LOW", "HIGH", "present", "ABSENT", "reported")
    assert M["records"] == sum(m["records"] for m in M["per_day"])
    month.write(M, str(tmp_path), "test", carried10["out"])
    text = (tmp_path / "evidence_checks.md").read_text()
    assert "## The chains" in text and "M15" in text
    assert os.path.exists(os.path.join(carried10["out"], "month_day_metrics.csv"))
