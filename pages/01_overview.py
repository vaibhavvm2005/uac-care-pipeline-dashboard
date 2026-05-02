"""
p01_overview.py
===============
Page 1: System Overview
- KPI scorecards
- Pipeline flow model
- Alert thresholds
- HHS census time series
- Monthly volume chart
"""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import COLORS
from utils.data_loader import load_processed, monthly_summary, system_kpis
from utils.metrics import get_status
from utils.charts import (
    hhs_census_chart,
    pipeline_flow_bar,
    backlog_area_chart,
    discharge_histogram,
)


def render():
    # ── Page Header ──────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="margin-bottom:24px">
          <div style="font-family:Syne,sans-serif; font-weight:800; font-size:22px;
                      color:{COLORS['text']}; letter-spacing:-0.01em">
            System Overview
          </div>
          <div style="font-size:11px; color:{COLORS['muted']}; margin-top:4px;
                      font-family:'DM Mono',monospace">
            Care pipeline health at a glance · Jan 2023 – Dec 2025
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Load Data ─────────────────────────────────────────────────────────────
    df      = load_processed()
    monthly = monthly_summary()
    kpis    = system_kpis()

    # ── Alert Banner ──────────────────────────────────────────────────────────
    census_status = get_status("hhs_census", kpis["current_hhs_care"])
    eff_status    = get_status("transfer_eff", kpis["recent_transfer_eff"] / 100)

    if kpis["current_hhs_care"] > 8000:
        st.error(f"🔴 **HHS Census SURGE** — {kpis['current_hhs_care']:,} children in care (>8,000 threshold). Surge protocol recommended.")
    elif kpis["current_hhs_care"] > 4000:
        st.warning(f"🟡 **HHS Census ELEVATED** — {kpis['current_hhs_care']:,} children in care. Monitor closely.")
    else:
        st.success(f"✅ **HHS Census NORMAL** — {kpis['current_hhs_care']:,} children in care as of {kpis['current_date']}.")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── KPI Scorecards ────────────────────────────────────────────────────────
    st.markdown(
        f"<div class='section-header'>KEY PERFORMANCE INDICATORS</div>",
        unsafe_allow_html=True,
    )

    r1c1, r1c2, r1c3, r1c4, r1c5, r1c6 = st.columns(6)

    with r1c1:
        st.metric(
            "Total Apprehended",
            f"{kpis['total_apprehended']:,}",
            delta="3-year total",
            delta_color="off",
        )
    with r1c2:
        st.metric(
            "CBP→HHS Transfers",
            f"{kpis['total_transferred']:,}",
            delta="3-year total",
            delta_color="off",
        )
    with r1c3:
        st.metric(
            "Sponsor Placements",
            f"{kpis['total_discharged']:,}",
            delta="3-year total",
            delta_color="off",
        )
    with r1c4:
        st.metric(
            "Current HHS Census",
            f"{kpis['current_hhs_care']:,}",
            delta=f"{kpis['pct_change_from_peak']:.1f}% from peak",
            delta_color="inverse",
            help=f"As of {kpis['current_date']}",
        )
    with r1c5:
        st.metric(
            "Peak HHS Census",
            f"{kpis['peak_hhs_care']:,}",
            delta=kpis["peak_hhs_date"],
            delta_color="off",
            help="Highest single-day census on record",
        )
    with r1c6:
        st.metric(
            "Avg Transfer Eff.",
            f"{kpis['avg_transfer_eff']}%",
            delta="3-year avg | Target ≥75%",
            delta_color="off",
        )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Pipeline Flow Diagram ─────────────────────────────────────────────────
    st.markdown(
        f"<div class='section-header'>CARE PIPELINE — LATEST SNAPSHOT ({kpis['current_date']})</div>",
        unsafe_allow_html=True,
    )

    pc1, pa1, pc2, pa2, pc3 = st.columns([3, 1, 3, 1, 3])

    def _stage_card(title, icon, count, sub, color, container):
        container.markdown(
            f"""
            <div style="background:{COLORS['surface2']}; border:1px solid {COLORS['border']};
                        border-top:3px solid {color}; border-radius:8px;
                        padding:16px 14px; text-align:center">
              <div style="font-size:28px; margin-bottom:8px">{icon}</div>
              <div style="font-size:9px; letter-spacing:0.14em; text-transform:uppercase;
                          color:{COLORS['muted']}; font-family:'DM Mono',monospace; margin-bottom:6px">
                {title}
              </div>
              <div style="font-family:Syne,sans-serif; font-size:28px; font-weight:800;
                          color:{color}; line-height:1">{count}</div>
              <div style="font-size:9px; color:{COLORS['muted']}; margin-top:6px;
                          font-family:'DM Mono',monospace">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def _arrow_card(label, container):
        container.markdown(
            f"""
            <div style="display:flex; flex-direction:column; align-items:center;
                        justify-content:center; height:100%; padding-top:30px; gap:4px">
              <div style="font-size:9px; color:{COLORS['blue']}; font-family:'DM Mono',monospace">
                {label}
              </div>
              <div style="font-size:20px; color:{COLORS['blue']}">→</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    _stage_card("CBP Custody", "🛡️",
                f"{kpis['latest_cbp_custody']:,}",
                "Active CBP caseload",
                COLORS["orange"], pc1)

    _arrow_card(f"{kpis['latest_cbp_transfer']:,}/day", pa1)

    _stage_card("HHS Care", "🏥",
                f"{kpis['current_hhs_care']:,}",
                "Active ORR shelter care",
                COLORS["yellow"], pc2)

    _arrow_card(f"{kpis['latest_hhs_discharge']:,}/day", pa2)

    _stage_card("Sponsor Placement", "🏠",
                f"{kpis['total_discharged']:,}",
                "Cumulative reunifications",
                COLORS["teal"], pc3)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── HHS Census Chart ──────────────────────────────────────────────────────
    st.markdown(
        "<div class='section-header'>HHS ACTIVE CENSUS OVER TIME</div>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(hhs_census_chart(df, height=340),
                    use_container_width=True, config={"displayModeBar": False})

    # ── Monthly Pipeline Volume ───────────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(
            "<div class='section-header'>MONTHLY PIPELINE VOLUME</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(pipeline_flow_bar(monthly, height=300),
                        use_container_width=True, config={"displayModeBar": False})

    with col_b:
        st.markdown(
            "<div class='section-header'>SYSTEM BACKLOG ACCUMULATION</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(backlog_area_chart(df, height=300),
                        use_container_width=True, config={"displayModeBar": False})

    # ── Key Findings ──────────────────────────────────────────────────────────
    st.markdown(
        "<div class='section-header' style='margin-top:20px'>KEY FINDINGS</div>",
        unsafe_allow_html=True,
    )

    findings = [
        (COLORS["red"],   "🔴 Peak Crisis Dec 2023",
         f"HHS census hit its all-time high of **{kpis['peak_hhs_care']:,} children** on {kpis['peak_hhs_date']}. "
         "This represents the most severe backlog in the 3-year dataset, coinciding with record daily transfer volumes."),
        (COLORS["teal"],  "✅ 83% Reduction Achieved",
         f"From the Dec 2023 peak of {kpis['peak_hhs_care']:,} to the current census of **{kpis['current_hhs_care']:,}** "
         f"({kpis['pct_change_from_peak']:.1f}% change). Reflects both reduced intake and sustained discharge operations throughout 2024–25."),
        (COLORS["yellow"], "🟡 Transfer Efficiency Drop 2025",
         "Transfer efficiency fell below **30%** in late 2025 — but with daily volumes under 15 children, "
         "absolute impact is limited. Ratio sensitivity increases at low volumes."),
        (COLORS["blue"],  "📊 System Now Stabilised",
         f"HHS census has held near **~2,400–2,500** since mid-2025, with slow organic growth from small "
         "daily intakes. System is in a new low-volume steady state."),
    ]

    f_cols = st.columns(2)
    for i, (color, title, body) in enumerate(findings):
        with f_cols[i % 2]:
            st.markdown(
                f"""
                <div style="background:{COLORS['surface2']}; border:1px solid {COLORS['border']};
                            border-left:3px solid {color}; border-radius:0 8px 8px 0;
                            padding:14px 16px; margin-bottom:12px">
                  <div style="font-family:Syne,sans-serif; font-size:12px; font-weight:700;
                              color:{COLORS['text']}; margin-bottom:6px">{title}</div>
                  <div style="font-size:11px; color:rgba(232,234,240,0.65);
                              font-family:'DM Mono',monospace; line-height:1.55">{body}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )