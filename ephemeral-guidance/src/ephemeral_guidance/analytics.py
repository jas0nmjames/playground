from __future__ import annotations

import duckdb

from .contracts import Tables


def build_rollups(*, con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.rollup_monthly_cashflow} AS
        SELECT
          date_trunc('month', txn_date) AS month,
          account_id,
          member_id,
          sum(CASE WHEN signed_amount > 0 THEN signed_amount ELSE 0 END) AS total_inflow,
          sum(CASE WHEN signed_amount < 0 THEN -signed_amount ELSE 0 END) AS total_outflow,
          sum(signed_amount) AS net_flow,
          count(*) AS txn_count
        FROM {Tables.curated_transactions}
        GROUP BY 1,2,3
        ORDER BY 1,2,3;
        """
    )

    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.rollup_spend_by_category_month} AS
        SELECT
          date_trunc('month', txn_date) AS month,
          category,
          sum(-signed_amount) AS total_spend,
          count(*) AS txn_count
        FROM {Tables.curated_transactions}
        WHERE signed_amount < 0
          AND category NOT IN ('transfer', 'credit_card_payment')
        GROUP BY 1,2
        ORDER BY 1, total_spend DESC;
        """
    )

    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.rollup_spend_by_member_month} AS
        SELECT
          date_trunc('month', txn_date) AS month,
          member_id,
          sum(-signed_amount) AS total_spend,
          count(*) AS txn_count
        FROM {Tables.curated_transactions}
        WHERE signed_amount < 0
          AND category NOT IN ('transfer', 'credit_card_payment')
        GROUP BY 1,2
        ORDER BY 1, total_spend DESC;
        """
    )

    con.execute(
        f"""
        CREATE OR REPLACE TABLE {Tables.rollup_spend_by_merchant_month} AS
        SELECT
          date_trunc('month', txn_date) AS month,
          merchant_canonical,
          any_value(merchant) AS merchant_display,
          sum(-signed_amount) AS total_spend,
          count(*) AS txn_count
        FROM {Tables.curated_transactions}
        WHERE signed_amount < 0
          AND category NOT IN ('transfer', 'credit_card_payment')
        GROUP BY 1,2
        ORDER BY 1, total_spend DESC;
        """
    )
