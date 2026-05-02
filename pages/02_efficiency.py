"""
p02_efficiency.py
=================
Page 2: Efficiency Analytics
- Transfer Efficiency Ratio trend
- Discharge Effectiveness Index trend
- Pipeline Throughput Rate
- Gauges for current period
- Weekday performance breakdown
- Year-over-year comparison
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import COLORS, PLOTLY_LAYOUT, THRESHOLDS
from utils.data_loader import load_processed, monthly_summary, system_kpis
from utils.metrics import get_status, compare_periods, weekday_performance
from utils.charts import (
    transfer_efficiency_chart,
    discharge_effectiveness_chart,
    throughput_bar_chart,
    kpi_gauge,
    weekday_heatmap,
    correlation_heatmap,
)


def render():
    st.markdown(
        f"""
        <div style="margin-bottom:24px">
          <div style="font-family:Syne,sans-serif; font-weight:800; font-size:22px;
                      color:{COLORS['text']}; letter-spacing:-0.01em">
            Efficiency Analytics
          </div>
          <div style="font-size:11px; color:{COLORS['muted']}; margin-top:4px;
                      font-family:'DM Mono',monospace">
            Transfer, discharge, and throughput efficiency KPIs with benchmarks
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Load Data ─────────────────────────────────────────────────────────────
    df      = load_processed()
    monthly = monthly_summary()
    kpis    = system_kpis()

    # ── Year Filter ───────────────────────────────────────────────────────────
    all_years = sorted(df["year"].unique().tolist())
    selected_years = st.multiselect(
        "Filter by year",
        options=all_years,
        default=all_years,
        key="eff_year_filter",
    )
    df_f      = df[df["year"].isin(selected_years)]
    monthly_f = monthly[monthly["year"].isin(selected_years)]

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Gauge Row ─────────────────────────────────────────────────────────────
    st.markdown(
        "<div class='section-header'>CURRENT EFFICIENCY GAUGES (30-DAY ROLLING)</div>",
        unsafe_allow_html=True,
    )

    g1, g2, g3, g4 = st.columns(4)
    te_recent  = df["transfer_efficiency"].tail(30).mean()
    de_recent  = df["discharge_effectiveness"].tail(30).mean()
    thr_recent = df["pipeline_throughput"].tail(30).mean()
    stab_recent= df["outcome_stability"].tail(30).mean()

    with g1:
        st.plotly_chart(kpi_gauge(
            te_recent, "Transfer Efficiency",
            min_val=0, max_val=1.5, target=0.75,
            suffix="×", height=200,
        ), use_container_width=True, config={"displayModeBar": False})
        s = get_status("transfer_eff", te_recent)
        st.markdown(
            f"<div style='text-align:center; font-size:10px; color:{s['color']}'>"
            f"{s['emoji']} {s['label']} — {te_recent:.1%}</div>",
            unsafe_allow_html=True,
        )

    with g2:
        st.plotly_chart(kpi_gauge(
            de_recent * 100, "Discharge Effectiveness",
            min_val=0, max_val=8, target=3.0,
            suffix="%", height=200,
        ), use_container_width=True, config={"displayModeBar": False})
        s = get_status("discharge_eff", de_recent)
        st.markdown(
            f"<div style='text-align:center; font-size:10px; color:{s['color']}'>"
            f"{s['emoji']} {s['label']} — {de_recent:.2%}</div>",
            unsafe_allow_html=True,
        )

    with g3:
        st.plotly_chart(kpi_gauge(
            thr_recent, "Pipeline Throughput",
            min_val=0, max_val=3, target=1.0,
            suffix="×", height=200,
        ), use_container_width=True, config={"displayModeBar": False})
        s = get_status("throughput", thr_recent)
        st.markdown(
            f"<div style='text-align:center; font-size:10px; color:{s['color']}'>"
            f"{s['emoji']} {s['label']} — {thr_recent:.2f}×</div>",
            unsafe_allow_html=True,
        )

    with g4:
        st.plotly_chart(kpi_gauge(
            stab_recent, "Outcome Stability",
            min_val=0, max_val=1, target=0.70,
            suffix="", height=200,
        ), use_container_width=True, config={"displayModeBar": False})
        s = get_status("outcome_stability", stab_recent)
        st.markdown(
            f"<div style='text-align:center; font-size:10px; color:{s['color']}'>"
            f"{s['emoji']} {s['label']} — {stab_recent:.3f}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Trend Charts ──────────────────────────────────────────────────────────
    st.markdown(
        "<div class='section-header'>EFFICIENCY TRENDS — MONTHLY AVERAGES</div>",
        unsafe_allow_html=True,
    )

    t1, t2 = st.columns(2)
    with t1:
        st.plotly_chart(
            transfer_efficiency_chart(monthly_f, height=280),
            use_container_width=True, config={"displayModeBar": False},
        )
    with t2:
        st.plotly_chart(
            discharge_effectiveness_chart(monthly_f, height=280),
            use_container_width=True, config={"displayModeBar": False},
        )

    st.plotly_chart(
        throughput_bar_chart(monthly_f, height=260),
        use_container_width=True, config={"displayModeBar": False},
    )

    # ── Weekday Analysis ──────────────────────────────────────────────────────
    st.markdown(
        "<div class='section-header' style='margin-top:12px'>WEEKDAY PERFORMANCE BREAKDOWN</div>",
        unsafe_allow_html=True,
    )

    wk1, wk2 = st.columns([2, 1])
    wk_df = weekday_performance(df_f)

    with wk1:
        st.plotly_chart(
            weekday_heatmap(wk_df, height=240),
            use_container_width=True, config={"displayModeBar": False},
        )

    with wk2:
        st.markdown(
            f"""
            <div style="background:{COLORS['surface2']}; border:1px solid {COLORS['border']};
                        border-radius:8px; padding:16px; margin-top:8px">
              <div style="font-size:9px; letter-spacing:0.12em; text-transform:uppercase;
                          color:{COLORS['muted']}; margin-bottom:12px">
                Weekday Summary
              </div>
            """,
            unsafe_allow_html=True,
        )
        for _, row in wk_df.iterrows():
            if pd.isna(row["avg_discharged"]):
                continue
            bar_pct = row["avg_discharged"] / wk_df["avg_discharged"].max() * 100 if wk_df["avg_discharged"].max() > 0 else 0
            st.markdown(
                f"""
                <div style="margin-bottom:8px">
                  <div style="display:flex; justify-content:space-between; margin-bottom:3px">
                    <span style="font-size:10px; color:{COLORS['text']}; font-family:'DM Mono',monospace">
                      {row['weekday'][:3]}
                    </span>
                    <span style="font-size:10px; color:{COLORS['teal']}; font-family:'DM Mono',monospace">
                      {row['avg_discharged']:.1f}/day
                    </span>
                  </div>
                  <div style="background:{COLORS['surface']}; border-radius:2px; height:4px">
                    <div style="background:{COLORS['teal']}; width:{bar_pct:.0f}%;
                                height:4px; border-radius:2px; opacity:0.8"></div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Year-over-Year Comparison ──────────────────────────────────────────────
    st.markdown(
        "<div class='section-header' style='margin-top:16px'>YEAR-OVER-YEAR COMPARISON</div>",
        unsafe_allow_html=True,
    )

    metrics_to_compare = {
        "transfer_efficiency":    ("Transfer Efficiency",    "higher"),
        "discharge_effectiveness":("Discharge Effectiveness","higher"),
        "pipeline_throughput":    ("Pipeline Throughput",    "higher"),
        "hhs_care":               ("HHS Census",             "lower"),
    }

    years = [str(y) for y in sorted(df["year"].unique())]
    yoy_data = []

    for col, (label, direction) in metrics_to_compare.items():
        row = {"Metric": label}
        for yr in years:
            subset = df[df["year"].astype(str) == yr][col].dropna()
            row[yr] = round(subset.mean(), 4)
        yoy_data.append(row)

    yoy_df = pd.DataFrame(yoy_data)

    # Style the dataframe
    def _style_val(val):
        if isinstance(val, float):
            return f"{val:,.4f}"
        return str(val)

    st.dataframe(
        yoy_df,
        use_container_width=True,
        hide_index=True,
    )

    # ── Correlation Heatmap ───────────────────────────────────────────────────
    with st.expander("📊 Metric Correlation Matrix", expanded=False):
        st.plotly_chart(
            correlation_heatmap(df_f, height=320),
            use_container_width=True, config={"displayModeBar": False},
        )
        st.markdown(
            f"""
            <div style="font-size:10px; color:{COLORS['muted']}; font-family:'DM Mono',monospace;
                        padding:8px 0">
              Strong positive correlation (→1.0) = metrics move together.<br>
              Strong negative correlation (→-1.0) = metrics move inversely.
            </div>
            """,
            unsafe_allow_html=True,
        )