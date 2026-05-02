"""
data_loader.py
==============
Handles all data ingestion, cleaning, type coercion, and feature engineering
for the UAC Care Pipeline Analytics dashboard.

Cached with st.cache_data so the CSV is read only once per session.
"""

import pandas as pd
import numpy as np
import streamlit as st
import sys
import os

# Allow imports from parent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import COL_MAP, DATA_PATH


# ── Raw Loader ───────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading UAC dataset…")
def load_raw() -> pd.DataFrame:
    """
    Read the CSV, rename columns, parse dates, coerce numerics.
    Returns a clean DataFrame with standardised column names.
    """
    df = pd.read_csv(DATA_PATH)

    # Drop fully-empty rows (trailing NaN rows in source file)
    df = df.dropna(subset=["Date"])

    # Rename columns to clean internal names
    df = df.rename(columns=COL_MAP)

    # Parse date
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    df = df.dropna(subset=["date"])

    # Clean HHS Care column — may contain comma-formatted strings e.g. "11,516"
    df["hhs_care"] = (
        df["hhs_care"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )

    # Coerce all numeric columns
    numeric_cols = ["cbp_apprehended", "cbp_custody", "cbp_transferred",
                    "hhs_care", "hhs_discharged"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Sort chronologically
    df = df.sort_values("date").reset_index(drop=True)

    return df


# ── Feature Engineering ──────────────────────────────────────────────────────

@st.cache_data(show_spinner="Computing pipeline metrics…")
def load_processed() -> pd.DataFrame:
    """
    Adds all derived KPI columns to the raw DataFrame.
    Calls load_raw() internally.
    """
    df = load_raw().copy()

    # ── Core KPI Ratios ──────────────────────────────────────────────────────
    # Transfer Efficiency Ratio: how fast is CBP moving children to HHS?
    df["transfer_efficiency"] = (
        df["cbp_transferred"] / df["cbp_custody"].replace(0, np.nan)
    ).round(4)

    # Discharge Effectiveness Index: what fraction of HHS children are placed daily?
    df["discharge_effectiveness"] = (
        df["hhs_discharged"] / df["hhs_care"].replace(0, np.nan)
    ).round(4)

    # Pipeline Throughput Rate: total exits / total entries
    total_exits   = df["cbp_transferred"] + df["hhs_discharged"]
    total_entries = df["cbp_apprehended"] + df["cbp_transferred"] + 1  # +1 avoids div/0
    df["pipeline_throughput"] = (total_exits / total_entries).round(4)

    # ── Backlog & Flow ───────────────────────────────────────────────────────
    df["system_backlog"]  = df["cbp_custody"] + df["hhs_care"]
    df["net_flow_hhs"]    = df["cbp_transferred"] - df["hhs_discharged"]

    # ── Time Components ──────────────────────────────────────────────────────
    df["year"]       = df["date"].dt.year
    df["month"]      = df["date"].dt.month
    df["month_str"]  = df["date"].dt.to_period("M").astype(str)
    df["week"]       = df["date"].dt.isocalendar().week.astype(int)
    df["weekday"]    = df["date"].dt.day_name()
    df["quarter"]    = df["date"].dt.to_period("Q").astype(str)
    df["is_weekend"] = df["date"].dt.weekday >= 5

    # ── Rolling Averages (7-day & 30-day) ───────────────────────────────────
    for window, suffix in [(7, "7d"), (30, "30d")]:
        df[f"hhs_care_ma{suffix}"]         = df["hhs_care"].rolling(window, min_periods=1).mean().round(0)
        df[f"transfer_efficiency_ma{suffix}"] = df["transfer_efficiency"].rolling(window, min_periods=1).mean().round(4)
        df[f"discharge_effectiveness_ma{suffix}"] = df["discharge_effectiveness"].rolling(window, min_periods=1).mean().round(4)
        df[f"hhs_discharged_ma{suffix}"]   = df["hhs_discharged"].rolling(window, min_periods=1).mean().round(1)

    # ── Backlog Delta (day-over-day change) ──────────────────────────────────
    df["backlog_delta"] = df["system_backlog"].diff()

    # ── Outcome Stability: rolling 30-day CV of discharge effectiveness ──────
    roll_std  = df["discharge_effectiveness"].rolling(30, min_periods=5).std()
    roll_mean = df["discharge_effectiveness"].rolling(30, min_periods=5).mean().replace(0, np.nan)
    df["outcome_stability"] = (1 - (roll_std / roll_mean)).clip(0, 1).round(4)

    # ── Threshold Status Labels ───────────────────────────────────────────────
    df["census_status"] = pd.cut(
        df["hhs_care"],
        bins=[0, 4000, 8000, 99999],
        labels=["Normal", "Elevated", "Surge"],
        right=True
    )

    df["transfer_status"] = pd.cut(
        df["transfer_efficiency"],
        bins=[0, 0.55, 0.75, 99],
        labels=["Critical", "Caution", "Good"],
        right=True
    )

    return df


# ── Aggregations ─────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def monthly_summary() -> pd.DataFrame:
    """
    Monthly aggregate of all key pipeline metrics.
    """
    df = load_processed()

    agg = df.groupby("month_str").agg(
        reporting_days         = ("date",                  "count"),
        cbp_apprehended_sum    = ("cbp_apprehended",       "sum"),
        cbp_transferred_sum    = ("cbp_transferred",       "sum"),
        hhs_discharged_sum     = ("hhs_discharged",        "sum"),
        hhs_care_avg           = ("hhs_care",              "mean"),
        hhs_care_max           = ("hhs_care",              "max"),
        cbp_custody_avg        = ("cbp_custody",           "mean"),
        transfer_eff_avg       = ("transfer_efficiency",   "mean"),
        transfer_eff_std       = ("transfer_efficiency",   "std"),
        discharge_eff_avg      = ("discharge_effectiveness","mean"),
        throughput_avg         = ("pipeline_throughput",   "mean"),
        backlog_avg            = ("system_backlog",        "mean"),
        net_flow_sum           = ("net_flow_hhs",          "sum"),
        outcome_stability_avg  = ("outcome_stability",     "mean"),
    ).reset_index()

    # Derived monthly ratios
    agg["transfer_eff_avg"]    = agg["transfer_eff_avg"].round(4)
    agg["discharge_eff_avg"]   = agg["discharge_eff_avg"].round(4)
    agg["throughput_avg"]      = agg["throughput_avg"].round(3)
    agg["hhs_care_avg"]        = agg["hhs_care_avg"].round(0)
    agg["cbp_custody_avg"]     = agg["cbp_custody_avg"].round(0)

    # Month label for display
    agg["month_label"] = pd.to_datetime(agg["month_str"]).dt.strftime("%b %Y")
    agg["year"]        = pd.to_datetime(agg["month_str"]).dt.year

    # Pipeline status per month
    def _status(row):
        if row["throughput_avg"] >= 1.3:  return "High Throughput"
        if row["throughput_avg"] >= 0.9:  return "Balanced"
        return "Backlog Risk"

    agg["pipeline_status"] = agg.apply(_status, axis=1)

    return agg


@st.cache_data(show_spinner=False)
def weekly_summary() -> pd.DataFrame:
    """Weekly aggregate for weekday vs weekend analysis."""
    df = load_processed()
    return df.groupby(["year", "week", "weekday"]).agg(
        avg_transfer_eff   = ("transfer_efficiency",    "mean"),
        avg_discharge_eff  = ("discharge_effectiveness","mean"),
        avg_discharged     = ("hhs_discharged",         "mean"),
        avg_transferred    = ("cbp_transferred",        "mean"),
    ).reset_index()


@st.cache_data(show_spinner=False)
def system_kpis() -> dict:
    """
    Compute all top-level scalar KPIs for the dashboard header cards.
    """
    df = load_processed()
    mo = monthly_summary()

    latest = df.iloc[-1]
    peak_idx = df["hhs_care"].idxmax()

    return {
        # Totals
        "total_apprehended":   int(df["cbp_apprehended"].sum()),
        "total_transferred":   int(df["cbp_transferred"].sum()),
        "total_discharged":    int(df["hhs_discharged"].sum()),
        "total_days":          len(df),

        # Census
        "current_hhs_care":   int(latest["hhs_care"]),
        "current_date":        latest["date"].strftime("%b %d, %Y"),
        "peak_hhs_care":       int(df["hhs_care"].max()),
        "peak_hhs_date":       df.loc[peak_idx, "date"].strftime("%b %d, %Y"),
        "pct_change_from_peak": round(
            (df["hhs_care"].iloc[-1] - df["hhs_care"].max()) / df["hhs_care"].max() * 100, 1
        ),

        # Efficiency averages
        "avg_transfer_eff":    round(df["transfer_efficiency"].mean() * 100, 1),
        "avg_discharge_eff":   round(df["discharge_effectiveness"].mean() * 100, 2),
        "avg_throughput":      round(df["pipeline_throughput"].mean(), 2),

        # Current (last 30-day avg)
        "recent_transfer_eff":  round(df["transfer_efficiency"].tail(30).mean() * 100, 1),
        "recent_discharge_eff": round(df["discharge_effectiveness"].tail(30).mean() * 100, 2),
        "recent_throughput":    round(df["pipeline_throughput"].tail(30).mean(), 2),

        # Backlog
        "current_backlog":     int(latest["system_backlog"]),
        "peak_backlog":        int(df["system_backlog"].max()),
        "backlog_trend":       "Decreasing" if df["system_backlog"].tail(14).diff().mean() < 0 else "Increasing",

        # Latest pipeline snapshot
        "latest_cbp_custody":  int(latest["cbp_custody"]),
        "latest_cbp_transfer": int(latest["cbp_transferred"]),
        "latest_hhs_discharge":int(latest["hhs_discharged"]),

        # Date range
        "date_start":  df["date"].min().strftime("%b %d, %Y"),
        "date_end":    df["date"].max().strftime("%b %d, %Y"),
    }