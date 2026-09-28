"""Generate a synthetic SaaS customer dataset for churn & retention analysis.

Reproducible: seed = 42. ~5,000 customers with realistic baked-in patterns:
- Basic monthly plans churn more than Pro/Enterprise.
- Startups churn more than Mid-market.
- More support tickets -> higher churn risk.
- Longer tenure protects against churn.
- Churned customers show longer login recency (a consequence, not a cause).

Output: data/customers.csv
"""

import numpy as np
import pandas as pd

SEED = 42
N = 5_000
TODAY = pd.Timestamp("2026-09-26")

rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------- signup dates
# 12 monthly cohorts: Oct 2025 .. Aug 2026
signup_start = pd.Timestamp("2025-10-01")
signup_end = pd.Timestamp("2026-08-31")
signup_dates = pd.to_datetime(
    rng.integers(signup_start.value // 10**9, signup_end.value // 10**9, N),
    unit="s",
).normalize()

# ------------------------------------------------------------------- segments
segments = rng.choice(
    ["Startup", "SMB", "Mid-market"], size=N, p=[0.45, 0.35, 0.20]
)

# ---------------------------------------------------------------------- plans
# Plan mix depends on segment (startups skew Basic, mid-market skew Enterprise)
plan_probs = {
    "Startup": [0.70, 0.25, 0.05],
    "SMB": [0.40, 0.45, 0.15],
    "Mid-market": [0.15, 0.45, 0.40],
}
plans = np.array(
    [rng.choice(["Basic", "Pro", "Enterprise"], p=plan_probs[s]) for s in segments]
)

# ------------------------------------------------------------ monthly revenue
base_rev = {"Basic": 1_200, "Pro": 4_500, "Enterprise": 18_000}
rev_sd = {"Basic": 200, "Pro": 600, "Enterprise": 3_000}
monthly_revenue = np.array(
    [max(200, rng.normal(base_rev[p], rev_sd[p])) for p in plans]
).round(0)

# -------------------------------------------------------------------- tenure
tenure_months = np.array(
    [max(1, (TODAY.year - d.year) * 12 + (TODAY.month - d.month)) for d in signup_dates]
)

# ------------------------------------------------------- support ticket volume
ticket_lambda = {"Basic": 2.2, "Pro": 1.3, "Enterprise": 0.8}
support_tickets = np.array(
    [rng.poisson(ticket_lambda[p]) for p in plans]
)

# ---------------------------------------------------------------- churn model
# Logistic model: plan, segment, tickets push churn up; tenure pushes it down.
plan_effect = {"Basic": 0.55, "Pro": 0.10, "Enterprise": -0.50}
seg_effect = {"Startup": 0.35, "SMB": 0.05, "Mid-market": -0.35}

logit = (
    -1.60
    + np.array([plan_effect[p] for p in plans])
    + np.array([seg_effect[s] for s in segments])
    + 0.22 * np.clip(support_tickets, 0, 6)
    - 0.09 * tenure_months
)
churn_prob = 1 / (1 + np.exp(-logit))
churned = (rng.random(N) < churn_prob).astype(int)

# ----------------------------------------------------------------- churn date
# Churned customers leave somewhere between day 15 and near-today.
churn_dates = []
for i in range(N):
    if churned[i] == 0:
        churn_dates.append(pd.NaT)
        continue
    max_day = max(20, (TODAY - signup_dates[i]).days - 5)
    churn_dates.append(signup_dates[i] + pd.Timedelta(days=int(rng.integers(15, max_day))))
churn_dates = pd.to_datetime(churn_dates)

# ------------------------------------------------------------ login recency
# Retained customers log in often; churned ones went quiet before leaving.
days_since_login = np.where(
    churned == 1,
    np.clip(rng.exponential(25, N).round(0) + 5, 1, 90),
    np.clip(rng.exponential(3, N).round(0) + 1, 1, 90),
).astype(int)

df = pd.DataFrame(
    {
        "customer_id": [f"CUST-{i:05d}" for i in range(1, N + 1)],
        "signup_date": signup_dates,
        "plan": plans,
        "segment": segments,
        "monthly_revenue": monthly_revenue,
        "tenure_months": tenure_months,
        "support_tickets_last_90d": support_tickets,
        "days_since_last_login": days_since_login,
        "churned": churned,
        "churn_date": churn_dates,
    }
).sort_values("signup_date").reset_index(drop=True)

df.to_csv("customers.csv", index=False)
print(f"Wrote customers.csv: {len(df):,} rows")
print(f"Overall churn rate: {df['churned'].mean():.1%}")
print(df.groupby("segment")["churned"].mean().round(3).to_string())
print(df.groupby("plan")["churned"].mean().round(3).to_string())
