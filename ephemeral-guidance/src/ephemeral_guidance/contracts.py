from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


CurrencyCode = Literal["USD"]

TxnType = Literal["debit", "credit"]
TxnStatus = Literal["posted"]


class FamilyMember(BaseModel):
    member_id: str
    first_name: str
    last_name: str
    role: str
    date_of_birth: Optional[str] = None
    age: Optional[int] = None


class Account(BaseModel):
    account_id: str
    account_name: str
    account_type: str
    institution: str
    account_number_masked: str
    owners: list[str]


class Transaction(BaseModel):
    transaction_id: str
    date: date
    time: time
    merchant: str
    amount: float
    currency: CurrencyCode = "USD"
    type: TxnType
    status: TxnStatus = "posted"
    transaction_type: str
    category: str
    raw_description: str
    clean_description: str
    account_id: str
    member_id: str
    tags: list[str] = Field(default_factory=list)
    running_balance: Optional[float] = None

    # convenience fields (curated)
    signed_amount: Optional[float] = None
    timestamp: Optional[datetime] = None
    merchant_canonical: Optional[str] = None


class InvestmentTransaction(BaseModel):
    investment_transaction_id: str
    date: date
    account_id: str
    member_id: str
    type: str
    sub_type: str
    ticker: str
    name: str
    shares: float
    price_per_share: float
    amount: float
    fees: float
    description: str


class HoldingSnapshotHolding(BaseModel):
    ticker: str
    name: str
    asset_class: str
    shares: float
    price_per_share: float
    market_value: float
    cost_basis: float
    gain_loss: float
    gain_loss_pct: float
    allocation_pct: float


class HoldingSnapshot(BaseModel):
    date: date
    account_id: str
    total_value: float
    total_cost_basis: float
    total_gain_loss: float
    total_gain_loss_pct: float
    holdings: list[HoldingSnapshotHolding]


class MonthlySummary(BaseModel):
    month: str  # YYYY-MM
    total_income: float
    total_expenses: float
    net_cashflow: float
    savings_rate_pct: float
    transaction_count: int
    expense_by_category: dict[str, float]


class NetWorth(BaseModel):
    as_of: str
    assets: dict[str, Any]
    liabilities: dict[str, Any]
    net_worth: float


class Tables:
    raw_family_members = "raw_family_members"
    raw_accounts = "raw_accounts"
    raw_transactions = "raw_transactions"
    raw_investment_transactions = "raw_investment_transactions"
    raw_holdings_snapshots = "raw_holdings_snapshots"
    raw_monthly_summaries = "raw_monthly_summaries"
    raw_net_worth = "raw_net_worth"

    curated_transactions = "curated_transactions"
    curated_accounts = "curated_accounts"
    curated_family_members = "curated_family_members"
    curated_investment_transactions = "curated_investment_transactions"
    curated_holdings_snapshots = "curated_holdings_snapshots"

    rollup_monthly_cashflow = "rollup_monthly_cashflow"
    rollup_spend_by_merchant_month = "rollup_spend_by_merchant_month"
    rollup_spend_by_category_month = "rollup_spend_by_category_month"
    rollup_spend_by_member_month = "rollup_spend_by_member_month"

    features_recurring_candidates = "features_recurring_candidates"
    features_anomaly_candidates = "features_anomaly_candidates"

    insights_candidates = "insights_candidates"
