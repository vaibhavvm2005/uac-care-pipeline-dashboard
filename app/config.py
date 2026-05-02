"""
config.py
=========
Global configuration: KPI thresholds, color palette, page settings,
and all constants shared across the UAC Care Pipeline Analytics dashboard.
"""

# ── App Identity ────────────────────────────────────────────────────────────
APP_TITLE       = "UAC Care Pipeline Analytics"
APP_SUBTITLE    = "U.S. HHS · Office of Refugee Resettlement"
APP_ICON        = "🏥"
APP_VERSION     = "1.0.0"
DATASET_PERIOD  = "January 2023 – December 2025"

# ── Data Source ──────────────────────────────────────────────────────────────
import os
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "HHS_UAC_Program.csv")

# ── Column Name Mappings (raw CSV → clean internal names) ───────────────────
COL_MAP = {
    "Date": "date",
    "Children apprehended and placed in CBP custody*": "cbp_apprehended",
    "Children in CBP custody": "cbp_custody",
    "Children transferred out of CBP custody": "cbp_transferred",
    "Children in HHS Care": "hhs_care",
    "Children discharged from HHS Care": "hhs_discharged",
}

# ── KPI Thresholds ───────────────────────────────────────────────────────────
THRESHOLDS = {
    # Transfer Efficiency Ratio (Transfers ÷ CBP Custody)
    "transfer_eff": {
        "green":  0.75,    # ≥ 75% → good
        "yellow": 0.55,    # 55–74% → caution
        "red":    0.00,    # < 55% → critical
        "label":  "Transfer Efficiency Ratio",
        "target": 0.75,
    },
    # Discharge Effectiveness Index (Discharges ÷ HHS Care)
    "discharge_eff": {
        "green":  0.030,
        "yellow": 0.020,
        "red":    0.000,
        "label":  "Discharge Effectiveness Index",
        "target": 0.030,
    },
    # Pipeline Throughput Rate
    "throughput": {
        "green":  1.0,
        "yellow": 0.80,
        "red":    0.00,
        "label":  "Pipeline Throughput Rate",
        "target": 1.0,
    },
    # HHS Census absolute level
    "hhs_census": {
        "green":  4000,    # < 4k → manageable
        "yellow": 8000,    # 4k–8k → elevated
        "red":    99999,   # > 8k → surge
        "label":  "HHS Active Census",
        "target": 4000,
    },
    # Outcome Stability Score (1 − CV)
    "outcome_stability": {
        "green":  0.70,
        "yellow": 0.50,
        "red":    0.00,
        "label":  "Outcome Stability Score",
        "target": 0.70,
    },
}

# ── Color Palette ────────────────────────────────────────────────────────────
COLORS = {
    "teal":        "#3dd6ac",
    "orange":      "#f06a3b",
    "blue":        "#5b8ef5",
    "yellow":      "#e8c84b",
    "red":         "#f04f4f",
    "muted":       "#5a6278",
    "bg":          "#0a0d13",
    "surface":     "#10141d",
    "surface2":    "#161b27",
    "text":        "#e8eaf0",
    "border":      "rgba(255,255,255,0.07)",
    # Semantic
    "green":       "#3dd6ac",    # success / good
    "warning":     "#e8c84b",    # caution
    "danger":      "#f04f4f",    # critical
    "info":        "#5b8ef5",    # neutral info
    # Series (for multi-line charts)
    "series": ["#3dd6ac", "#5b8ef5", "#f06a3b", "#e8c84b", "#f04f4f", "#a78bfa"],
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor = "rgba(0,0,0,0)",
    plot_bgcolor  = "rgba(0,0,0,0)",
    font          = dict(family="DM Mono, monospace", color=COLORS["muted"], size=11),
    margin        = dict(l=12, r=12, t=32, b=12),
    legend        = dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
    xaxis         = dict(gridcolor="rgba(255,255,255,0.05)", zeroline=False),
    yaxis         = dict(gridcolor="rgba(255,255,255,0.05)", zeroline=False),
)

# ── Rolling Window Sizes ─────────────────────────────────────────────────────
ROLLING = {
    "short": 7,    # 7-day rolling average
    "medium": 30,  # 30-day rolling average
    "long": 90,    # 90-day rolling average
}

# ── Alert Messages ───────────────────────────────────────────────────────────
ALERT_MESSAGES = {
    "hhs_surge":    "⚠️ HHS Census exceeds 8,000 — Surge Protocol Recommended",
    "hhs_elevated": "🟡 HHS Census elevated (4,000–8,000) — Monitor Closely",
    "hhs_normal":   "✅ HHS Census within normal range",
    "eff_critical": "🔴 Transfer Efficiency < 55% — CBP Coordination Review Needed",
    "eff_caution":  "🟡 Transfer Efficiency 55–74% — Monitor Pipeline",
    "eff_good":     "✅ Transfer Efficiency meets target (≥75%)",
    "backlog_grow": "⚠️ Backlog Growing — Net flow positive for 4+ weeks",
    "backlog_clear":"✅ Backlog Clearing — Net flow negative",
}

# ── Page Navigation ──────────────────────────────────────────────────────────
PAGES = [
    {"id": "overview",   "title": "System Overview",        "icon": "📊"},
    {"id": "efficiency", "title": "Efficiency Analytics",   "icon": "⚡"},
    {"id": "backlog",    "title": "Backlog Detection",       "icon": "📈"},
    {"id": "outcomes",   "title": "Outcome Trends",          "icon": "🎯"},
    {"id": "report",     "title": "Monthly Report",          "icon": "📋"},
]