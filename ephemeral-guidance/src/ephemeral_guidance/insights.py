from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import duckdb

from .contracts import Tables


def _stable_id(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()[:16]


@dataclass(frozen=True)
class InsightCard:
    insight_id: str
    kind: str
    title: str
    one_liner: str
    severity: float
    score: float
    time_window: dict[str, str] | None
    metrics: dict[str, Any]
    evidence: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "kind": self.kind,
            "title": self.title,
            "one_liner": self.one_liner,
            "severity": self.severity,
            "score": self.score,
            "time_window": self.time_window,
            "metrics": self.metrics,
            "evidence": self.evidence,
        }


def _fetchall_dict(con: duckdb.DuckDBPyConnection, sql: str, params: Iterable[Any] | None = None) -> list[dict[str, Any]]:
    cur = con.execute(sql, params or [])
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _iso(d: Any) -> str:
    if isinstance(d, (date,)):
        return d.isoformat()
    return str(d)


def build_insight_candidates(*, con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.insights_candidates} (
          insight_id VARCHAR,
          kind VARCHAR,
          title VARCHAR,
          one_liner VARCHAR,
          severity DOUBLE,
          score DOUBLE,
          time_window JSON,
          metrics JSON,
          evidence JSON
        );
        """
    )

    cards: list[InsightCard] = []

    # 1) Recurring merchants (subscriptions/bills)
    rec = _fetchall_dict(
        con,
        f"""
        SELECT *
        FROM {Tables.features_recurring_candidates}
        WHERE recurring_score >= 0.5
        ORDER BY recurring_score DESC, avg_amount DESC
        LIMIT 25
        """,
    )
    for r in rec:
        merchant = r["merchant_display"]
        avg_amount = float(r["avg_amount"])
        months = int(r["active_months"])
        score = float(r["recurring_score"])
        insight_id = f"rec_{_stable_id('recurring', r['account_id'], r['merchant_canonical'], r['category'])}"
        cards.append(
            InsightCard(
                insight_id=insight_id,
                kind="recurring",
                title=f"Recurring spend: {merchant}",
                one_liner=f"Appears in {months} months, about ${avg_amount:,.2f}/month.",
                severity=min(1.0, 0.4 + (avg_amount / 300.0)),
                score=score,
                time_window={"start_month": _iso(r["first_month"]), "end_month": _iso(r["last_month"])},
                metrics={
                    "avg_amount": avg_amount,
                    "active_months": months,
                    "amount_cv": float(r["amount_cv"]) if r["amount_cv"] is not None else None,
                    "txn_count": int(r["txn_count"]),
                },
                evidence={
                    "source_table": Tables.features_recurring_candidates,
                    "keys": {
                        "account_id": r["account_id"],
                        "merchant_canonical": r["merchant_canonical"],
                        "category": r["category"],
                    },
                },
            )
        )

    # 2) Anomalies (top scored)
    anoms = _fetchall_dict(
        con,
        f"""
        SELECT *
        FROM {Tables.features_anomaly_candidates}
        ORDER BY anomaly_score DESC, txn_date DESC
        LIMIT 25
        """,
    )
    for a in anoms:
        amt = float(a["amt"])
        merchant = a["merchant_display"]
        reason = a["reason"] or "anomaly"
        score = float(a["anomaly_score"])
        insight_id = f"anom_{_stable_id('anomaly', str(a['transaction_id']))}"
        cards.append(
            InsightCard(
                insight_id=insight_id,
                kind="anomaly",
                title=f"Unusual charge: {merchant}",
                one_liner=f"${amt:,.2f} flagged as {reason}.",
                severity=score,
                score=score,
                time_window={"date": _iso(a["txn_date"])},
                metrics={
                    "amount": amt,
                    "z": float(a["z"]) if a["z"] is not None else None,
                    "reason": reason,
                    "category": a["category"],
                },
                evidence={
                    "source_table": Tables.features_anomaly_candidates,
                    "keys": {"transaction_id": a["transaction_id"]},
                },
            )
        )

    # 3) Biggest category deltas (month-over-month)
    deltas = _fetchall_dict(
        con,
        f"""
        WITH by_cat AS (
          SELECT month, category, total_spend
          FROM {Tables.rollup_spend_by_category_month}
        ),
        joined AS (
          SELECT
            curr.month AS month,
            curr.category AS category,
            curr.total_spend AS spend,
            prev.total_spend AS prev_spend,
            (curr.total_spend - prev.total_spend) AS delta
          FROM by_cat curr
          LEFT JOIN by_cat prev
            ON prev.category = curr.category
           AND prev.month = (curr.month - INTERVAL 1 MONTH)
        )
        SELECT *
        FROM joined
        WHERE prev_spend IS NOT NULL
        ORDER BY delta DESC
        LIMIT 25
        """,
    )
    for d in deltas:
        delta = float(d["delta"])
        if delta <= 0:
            continue
        cat = d["category"]
        month = d["month"]
        spend = float(d["spend"])
        prev = float(d["prev_spend"])
        score = min(1.0, delta / 500.0)
        insight_id = f"delta_{_stable_id('category_delta', _iso(month), cat)}"
        cards.append(
            InsightCard(
                insight_id=insight_id,
                kind="category_delta",
                title=f"Spending increased in {cat}",
                one_liner=f"{_iso(month)[:7]}: +${delta:,.2f} vs prior month (${prev:,.2f} → ${spend:,.2f}).",
                severity=score,
                score=score,
                time_window={"month": _iso(month)},
                metrics={"delta": delta, "spend": spend, "prev_spend": prev, "category": cat},
                evidence={
                    "source_table": Tables.rollup_spend_by_category_month,
                    "keys": {"month": _iso(month), "category": cat},
                },
            )
        )

    # Insert into DuckDB
    con.executemany(
        f"""
        INSERT INTO {Tables.insights_candidates}
          (insight_id, kind, title, one_liner, severity, score, time_window, metrics, evidence)
        VALUES (?, ?, ?, ?, ?, ?, ?::JSON, ?::JSON, ?::JSON)
        """,
        [
            (
                c.insight_id,
                c.kind,
                c.title,
                c.one_liner,
                float(c.severity),
                float(c.score),
                json.dumps(c.time_window) if c.time_window is not None else json.dumps(None),
                json.dumps(c.metrics),
                json.dumps(c.evidence),
            )
            for c in cards
        ],
    )


def export_insights_json(
    *,
    con: duckdb.DuckDBPyConnection,
    out_path: Path,
    limit: int = 60,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cards = _fetchall_dict(
        con,
        f"""
        SELECT
          insight_id,
          kind,
          title,
          one_liner,
          severity,
          score,
          time_window::VARCHAR AS time_window,
          metrics::VARCHAR AS metrics,
          evidence::VARCHAR AS evidence
        FROM {Tables.insights_candidates}
        ORDER BY score DESC, severity DESC, insight_id ASC
        LIMIT ?
        """,
        [limit],
    )
    normalized = []
    for c in cards:
        normalized.append(
            {
                "insight_id": c["insight_id"],
                "kind": c["kind"],
                "title": c["title"],
                "one_liner": c["one_liner"],
                "severity": float(c["severity"]),
                "score": float(c["score"]),
                "time_window": json.loads(c["time_window"]) if c["time_window"] else None,
                "metrics": json.loads(c["metrics"]) if c["metrics"] else {},
                "evidence": json.loads(c["evidence"]) if c["evidence"] else {},
            }
        )
    out_path.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
