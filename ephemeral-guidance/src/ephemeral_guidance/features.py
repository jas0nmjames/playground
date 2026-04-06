from __future__ import annotations

import duckdb

from .contracts import Tables


def build_recurring_candidates(*, con: duckdb.DuckDBPyConnection) -> None:
    # Heuristic: recurring if it occurs in many distinct months with low amount variance
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.features_recurring_candidates} AS
        WITH base AS (
          SELECT
            account_id,
            merchant_canonical,
            merchant AS merchant_display,
            category,
            date_trunc('month', txn_date) AS month,
            abs(signed_amount) AS amt
          FROM {Tables.curated_transactions}
          WHERE signed_amount < 0
            AND category NOT IN ('transfer', 'credit_card_payment')
        ),
        agg AS (
          SELECT
            account_id,
            merchant_canonical,
            any_value(merchant_display) AS merchant_display,
            category,
            count(*) AS txn_count,
            count(DISTINCT month) AS active_months,
            avg(amt) AS avg_amount,
            stddev_pop(amt) AS std_amount,
            min(month) AS first_month,
            max(month) AS last_month
          FROM base
          GROUP BY 1,2,4
        )
        SELECT
          *,
          CASE
            WHEN avg_amount > 0 THEN coalesce(std_amount, 0) / avg_amount
            ELSE NULL
          END AS amount_cv,
          CASE
            WHEN active_months >= 8 AND (coalesce(std_amount, 0) / nullif(avg_amount,0)) <= 0.08 THEN 0.9
            WHEN active_months >= 6 AND (coalesce(std_amount, 0) / nullif(avg_amount,0)) <= 0.12 THEN 0.7
            WHEN active_months >= 4 AND (coalesce(std_amount, 0) / nullif(avg_amount,0)) <= 0.15 THEN 0.5
            ELSE 0.0
          END AS recurring_score
        FROM agg
        WHERE active_months >= 4
        ORDER BY recurring_score DESC, avg_amount DESC;
        """
    )


def build_anomaly_candidates(*, con: duckdb.DuckDBPyConnection) -> None:
    # Simple z-score outliers within (merchant_canonical, category)
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.features_anomaly_candidates} AS
        WITH debits AS (
          SELECT
            transaction_id,
            txn_date,
            account_id,
            member_id,
            merchant_canonical,
            merchant,
            category,
            abs(signed_amount) AS amt
          FROM {Tables.curated_transactions}
          WHERE signed_amount < 0
            AND category NOT IN ('transfer', 'credit_card_payment')
        ),
        stats AS (
          SELECT
            merchant_canonical,
            category,
            count(*) AS n,
            avg(amt) AS mean_amt,
            stddev_pop(amt) AS std_amt
          FROM debits
          GROUP BY 1,2
          HAVING count(*) >= 10
        ),
        scored AS (
          SELECT
            d.*,
            s.n,
            s.mean_amt,
            s.std_amt,
            CASE
              WHEN s.std_amt IS NULL OR s.std_amt = 0 THEN NULL
              ELSE (d.amt - s.mean_amt) / s.std_amt
            END AS z
          FROM debits d
          LEFT JOIN stats s
            ON d.merchant_canonical = s.merchant_canonical
           AND d.category = s.category
        )
        SELECT
          transaction_id,
          txn_date,
          account_id,
          member_id,
          merchant_canonical,
          merchant AS merchant_display,
          category,
          amt,
          z,
          CASE
            WHEN category = 'fees' THEN 0.9
            WHEN z >= 4 THEN 0.85
            WHEN z >= 3 THEN 0.65
            ELSE 0.0
          END AS anomaly_score,
          CASE
            WHEN category = 'fees' THEN 'fee_detected'
            WHEN z >= 4 THEN 'high_outlier'
            WHEN z >= 3 THEN 'outlier'
            ELSE NULL
          END AS reason
        FROM scored
        WHERE category = 'fees' OR z >= 3
        ORDER BY anomaly_score DESC, txn_date DESC;
        """
    )


def build_features(*, con: duckdb.DuckDBPyConnection) -> None:
    build_recurring_candidates(con=con)
    build_anomaly_candidates(con=con)
