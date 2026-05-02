"""
metrics.py
==========
All KPI computation, threshold evaluation, and statistical analysis
functions for the UAC Care Pipeline Analytics dashboard.
"""

import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import THRESHOLDS, COLORS


# ── Threshold Evaluation ─────────────────────────────────────────────────────

def get_status(metric: str, value: float) -> dict:
    """
    Returns status dict: {'color': hex, 'label': str, 'emoji': str}
    for a given KPI metric and value.
    """
    t = THRESHOLDS.get(metric)
    if t is None:
        return {"color": COLORS["muted"], "label": "Unknown", "emoji": "⬜"}

    # census_status: lower is better
    if metric == "hhs_census":
        if value < t["green"]:
            return {"color": COLORS["green"],   "label": "Normal",   "emoji": "✅"}
        elif value < t["yellow"]:
            return {"color": COLORS["warning"],  "label": "Elevated", "emoji": "🟡"}
        else:
            return {"color": COLORS["danger"],   "label": "Surge",    "emoji": "🔴"}

    # All others: higher is better
    if value >= t["green"]:
        return {"color": COLORS["green"],   "label": "Good",     "emoji": "✅"}
    elif value >= t["yellow"]:
        return {"color": COLORS["warning"],  "label": "Caution",  "emoji": "🟡"}
    else:
        return {"color": COLORS["danger"],   "label": "Critical", "emoji": "🔴"}


def delta_arrow(current: float, previous: float, higher_is_better: bool = True) -> str:
    """Returns ↑ / ↓ / → arrow string with sign for metric delta."""
    if previous == 0 or pd.isna(previous):
        return "→"
    delta = current - previous
    pct   = abs(delta) / abs(previous) * 100
    if abs(pct) < 1:
        return f"→ {delta:+.1f}"
    arrow = "↑" if delta > 0 else "↓"
    color_arrow = arrow if (delta > 0) == higher_is_better else arrow
    return f"{color_arrow} {abs(pct):.1f}%"


# ── Efficiency Metrics ───────────────────────────────────────────────────────

def compute_transfer_efficiency(transfers: pd.Series, cbp_custody: pd.Series) -> pd.Series:
    """Transfer Efficiency Ratio = Transfers ÷ CBP Custody."""
    return (transfers / cbp_custody.replace(0, np.nan)).round(4)


def compute_discharge_effectiveness(discharged: pd.Series, hhs_care: pd.Series) -> pd.Series:
    """Discharge Effectiveness = Discharges ÷ HHS Care."""
    return (discharged / hhs_care.replace(0, np.nan)).round(4)


def compute_pipeline_throughput(
    transferred: pd.Series,
    discharged: pd.Series,
    apprehended: pd.Series
) -> pd.Series:
    """Pipeline Throughput = (Transfers + Discharges) ÷ (Apprehended + Transfers + 1)."""
    exits   = transferred + discharged
    entries = apprehended + transferred + 1
    return (exits / entries).round(4)


def compute_outcome_stability(discharge_eff: pd.Series, window: int = 30) -> pd.Series:
    """
    Outcome Stability Score = 1 − CV(discharge_effectiveness)
    CV = std / mean over a rolling window.
    Higher = more consistent placements.
    """
    roll_std  = discharge_eff.rolling(window, min_periods=5).std()
    roll_mean = discharge_eff.rolling(window, min_periods=5).mean().replace(0, np.nan)
    cv = roll_std / roll_mean
    return (1 - cv).clip(0, 1).round(4)


def compute_backlog_accumulation_rate(backlog: pd.Series, window: int = 7) -> pd.Series:
    """
    Backlog Accumulation Rate = 7-day rolling mean of daily backlog delta.
    Negative = backlog shrinking (good). Positive = growing (bad).
    """
    return backlog.diff().rolling(window, min_periods=1).mean().round(1)


# ── Bottleneck Detection ──────────────────────────────────────────────────────

def detect_bottleneck_periods(df: pd.DataFrame, consecutive_days: int = 14) -> pd.DataFrame:
    """
    Identifies periods where net_flow_hhs > 0 for `consecutive_days` in a row.
    (More transfers in than discharges out → backlog growing.)
    Returns DataFrame of bottleneck periods with start/end/duration.
    """
    df = df.copy()
    df["is_positive_flow"] = df["net_flow_hhs"] > 0

    periods = []
    in_period = False
    start_idx = None

    for i, row in df.iterrows():
        if row["is_positive_flow"] and not in_period:
            in_period  = True
            start_idx  = i
        elif not row["is_positive_flow"] and in_period:
            duration = (df.loc[i, "date"] - df.loc[start_idx, "date"]).days
            if duration >= consecutive_days:
                periods.append({
                    "start_date": df.loc[start_idx, "date"],
                    "end_date":   df.loc[i, "date"],
                    "duration_days": duration,
                    "peak_backlog": df.loc[start_idx:i, "system_backlog"].max(),
                    "total_net_inflow": df.loc[start_idx:i, "net_flow_hhs"].sum(),
                })
            in_period = False

    return pd.DataFrame(periods)


def identify_stagnation_periods(df: pd.DataFrame, threshold: float = 0.01,
                                window: int = 14) -> pd.DataFrame:
    """
    Identifies periods where discharge_effectiveness < threshold
    for `window` consecutive days — suggesting placement stagnation.
    """
    df = df.copy()
    df["low_discharge"] = df["discharge_effectiveness"] < threshold

    periods = []
    in_period = False
    start_idx = None

    for i, row in df.iterrows():
        if row["low_discharge"] and not in_period:
            in_period = True
            start_idx = i
        elif not row["low_discharge"] and in_period:
            duration = (df.loc[i, "date"] - df.loc[start_idx, "date"]).days
            if duration >= window:
                periods.append({
                    "start_date":    df.loc[start_idx, "date"],
                    "end_date":      df.loc[i, "date"],
                    "duration_days": duration,
                    "avg_discharge_eff": df.loc[start_idx:i, "discharge_effectiveness"].mean(),
                })
            in_period = False

    return pd.DataFrame(periods)


# ── Comparative Stats ─────────────────────────────────────────────────────────

def compare_periods(df: pd.DataFrame, col: str,
                    period_a: str, period_b: str) -> dict:
    """
    Compare a metric column between two year periods.
    period_a, period_b: '2023', '2024', '2025', etc.
    Returns dict with means, delta, and percent change.
    """
    a = df[df["year"].astype(str) == period_a][col].dropna()
    b = df[df["year"].astype(str) == period_b][col].dropna()
    mean_a = a.mean()
    mean_b = b.mean()
    delta  = mean_b - mean_a
    pct_ch = (delta / abs(mean_a) * 100) if mean_a != 0 else np.nan
    return {
        "period_a": period_a, "mean_a": round(mean_a, 4),
        "period_b": period_b, "mean_b": round(mean_b, 4),
        "delta": round(delta, 4),
        "pct_change": round(pct_ch, 1),
        "direction": "improved" if delta > 0 else "declined",
    }


def weekday_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Average discharge effectiveness by day of week.
    Useful for staffing / scheduling recommendations.
    """
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    result = (
        df.groupby("weekday")
        .agg(
            avg_discharged      = ("hhs_discharged",        "mean"),
            avg_discharge_eff   = ("discharge_effectiveness","mean"),
            avg_transfer_eff    = ("transfer_efficiency",   "mean"),
            days_count          = ("date",                   "count"),
        )
        .reindex(order)
        .reset_index()
    )
    result["avg_discharged"]    = result["avg_discharged"].round(1)
    result["avg_discharge_eff"] = result["avg_discharge_eff"].round(4)
    result["avg_transfer_eff"]  = result["avg_transfer_eff"].round(4)
    return result


def rolling_correlation(df: pd.DataFrame, col_a: str, col_b: str,
                        window: int = 30) -> pd.Series:
    """30-day rolling Pearson correlation between two series."""
    return df[col_a].rolling(window, min_periods=10).corr(df[col_b]).round(3)


def summary_statistics(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """
    Returns a formatted descriptive statistics table
    for the given columns.
    """
    stats = df[cols].describe().T
    stats["CV (%)"] = (stats["std"] / stats["mean"] * 100).round(1)
    return stats.round(3)