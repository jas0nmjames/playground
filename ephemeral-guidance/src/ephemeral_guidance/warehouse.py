from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb

from .contracts import Tables


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def connect(db_path: Path) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute("PRAGMA threads=4")
    con.execute("PRAGMA enable_progress_bar=false")
    return con


def build_warehouse(
    *,
    con: duckdb.DuckDBPyConnection,
    assets_dir: Path,
) -> None:
    """
    Load JSON assets into DuckDB raw_* tables, then materialize curated_* tables.
    Deterministic and idempotent (uses CREATE OR REPLACE).
    """
    transactions_path = assets_dir / "transactions.json"
    accounts_path = assets_dir / "accounts.json"
    family_members_path = assets_dir / "family_members.json"
    investment_txns_path = assets_dir / "investment_transactions.json"
    holdings_snaps_path = assets_dir / "holdings_snapshots.json"
    monthly_summaries_path = assets_dir / "monthly_summaries.json"
    net_worth_path = assets_dir / "net_worth.json"

    for p in [
        transactions_path,
        accounts_path,
        family_members_path,
        investment_txns_path,
        holdings_snaps_path,
        monthly_summaries_path,
        net_worth_path,
    ]:
        if not p.exists():
            raise FileNotFoundError(str(p))

    # Raw tables that are simple JSON arrays
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.raw_transactions} AS
        SELECT * FROM read_json_auto('{transactions_path.as_posix()}');
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.raw_accounts} AS
        SELECT * FROM read_json_auto('{accounts_path.as_posix()}');
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.raw_family_members} AS
        SELECT * FROM read_json_auto('{family_members_path.as_posix()}');
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.raw_investment_transactions} AS
        SELECT * FROM read_json_auto('{investment_txns_path.as_posix()}');
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.raw_monthly_summaries} AS
        SELECT * FROM read_json_auto('{monthly_summaries_path.as_posix()}');
        """
    )

    # Raw net worth: single dict → single-row table
    net_worth = _read_json(net_worth_path)
    con.execute(f"CREATE OR REPLACE TABLE {Tables.raw_net_worth} (doc JSON)")
    con.execute(
        f"INSERT INTO {Tables.raw_net_worth} VALUES (?)",
        [json.dumps(net_worth)],
    )

    # Raw holdings snapshots: dict[account_id] -> list[snapshots]
    snaps = _read_json(holdings_snaps_path)
    rows: list[dict[str, Any]] = []
    for account_id, snapshots in snaps.items():
        for s in snapshots:
            rows.append(
                {
                    "account_id": account_id,
                    "date": s.get("date"),
                    "total_value": s.get("total_value"),
                    "total_cost_basis": s.get("total_cost_basis"),
                    "total_gain_loss": s.get("total_gain_loss"),
                    "total_gain_loss_pct": s.get("total_gain_loss_pct"),
                    "holdings": json.dumps(s.get("holdings", [])),
                }
            )

    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.raw_holdings_snapshots} (
          account_id VARCHAR,
          date VARCHAR,
          total_value DOUBLE,
          total_cost_basis DOUBLE,
          total_gain_loss DOUBLE,
          total_gain_loss_pct DOUBLE,
          holdings VARCHAR
        );
        """
    )
    con.executemany(
        f"""
        INSERT INTO {Tables.raw_holdings_snapshots}
          (account_id, date, total_value, total_cost_basis, total_gain_loss, total_gain_loss_pct, holdings)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                r["account_id"],
                r["date"],
                r["total_value"],
                r["total_cost_basis"],
                r["total_gain_loss"],
                r["total_gain_loss_pct"],
                r["holdings"],
            )
            for r in rows
        ],
    )

    # Curated: normalize common types + add signed_amount + timestamp + canonical merchant
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.curated_transactions} AS
        WITH base AS (
          SELECT
            transaction_id,
            CAST(date AS DATE) AS txn_date,
            CAST(time AS TIME) AS txn_time,
            CAST(date || ' ' || time AS TIMESTAMP) AS txn_ts,
            account_id,
            member_id,
            merchant,
            clean_description,
            raw_description,
            category,
            transaction_type,
            CAST(amount AS DOUBLE) AS amount,
            currency,
            type AS dr_cr,
            status,
            tags,
            CAST(running_balance AS DOUBLE) AS running_balance
          FROM {Tables.raw_transactions}
        )
        SELECT
          *,
          CASE WHEN dr_cr = 'debit' THEN -amount ELSE amount END AS signed_amount,
          lower(regexp_replace(trim(merchant), '\\\\s+', ' ', 'g')) AS merchant_canonical
        FROM base;
        """
    )

    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.curated_accounts} AS
        SELECT
          account_id,
          account_name,
          account_type,
          institution,
          account_number_masked,
          owners,
          TRY_CAST(opening_balance AS DOUBLE) AS opening_balance,
          TRY_CAST(interest_rate AS DOUBLE) AS interest_rate,
          TRY_CAST(credit_limit AS DOUBLE) AS credit_limit
        FROM {Tables.raw_accounts};
        """
    )

    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.curated_family_members} AS
        SELECT
          member_id,
          first_name,
          last_name,
          role,
          date_of_birth,
          TRY_CAST(age AS INTEGER) AS age
        FROM {Tables.raw_family_members};
        """
    )

    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.curated_investment_transactions} AS
        SELECT
          investment_transaction_id,
          CAST(date AS DATE) AS txn_date,
          account_id,
          member_id,
          type,
          sub_type,
          ticker,
          name,
          TRY_CAST(shares AS DOUBLE) AS shares,
          TRY_CAST(price_per_share AS DOUBLE) AS price_per_share,
          TRY_CAST(amount AS DOUBLE) AS amount,
          TRY_CAST(fees AS DOUBLE) AS fees,
          description
        FROM {Tables.raw_investment_transactions};
        """
    )

    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.curated_holdings_snapshots} AS
        SELECT
          account_id,
          CAST(date AS DATE) AS snap_date,
          TRY_CAST(total_value AS DOUBLE) AS total_value,
          TRY_CAST(total_cost_basis AS DOUBLE) AS total_cost_basis,
          TRY_CAST(total_gain_loss AS DOUBLE) AS total_gain_loss,
          TRY_CAST(total_gain_loss_pct AS DOUBLE) AS total_gain_loss_pct,
          holdings::JSON AS holdings
        FROM {Tables.raw_holdings_snapshots};
        """
    )
