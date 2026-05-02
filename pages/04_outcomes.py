"""
p04_outcomes.py
===============
Page 4: Placement Outcome Trends
- Outcome stability score over time
- Monthly discharge volume trend
- Discharge distribution histogram
- Year-over-year placement comparison
- Rolling average discharge analysis
- Descriptive statistics table
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import COLORS
from utils.data_loader import load_processed, monthly_summary, system_kpis
from utils.metrics import compare_periods, summary_statistics
from utils.charts import (
    outcome_stability_chart,
    discharge_histogram,
    discharge_effectiveness_chart,
)


def render():
    st.markdown(
        f"""
        <div style="margin-bottom:24px">
          <div style="font-family:Syne,sans-serif; font-weight:800; font-size:22px;
                      color:{COLORS['text']}; letter-spacing:-0.01em">
            Placement Outcome Trends
          </div>
          <div style="font-size:11px; color:{COLORS['muted']}; margin-top:4px;
                      font-family:'DM Mono',monospace">
            Sponsor reunification consistency, discharge patterns & outcome stability
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df      = load_processed()
    monthly = monthly_summary()
    kpis    = system_kpis()

    # ── Summary Row ───────────────────────────────────────────────────────────
    st.markdown(
        "<div class='section-header'>PLACEMENT OUTCOME SUMMARY</div>",
        unsafe_allow_html=True,
    )

    o1, o2, o3, o4 = st.columns(4)
    total_disc   = int(df["hhs_discharged"].sum())
    avg_daily    = df["hhs_discharged"].mean()
    max_daily    = int(df["hhs_discharged"].max())
    stab_now     = df["outcome_stability"].dropna().iloc[-1] if df["outcome_stability"].dropna().shape[0] > 0 else 0

    # Best discharge month
    best_mo = monthly.loc[monthly["hhs_discharged_sum"].idxmax()]

    with o1:
        st.metric("Total Sponsor Placements", f"{total_disc:,}",
                  delta="3-year cumulative", delta_color="off")
    with o2:
        st.metric("Avg Daily Discharges", f"{avg_daily:.1f}",
                  delta="per reporting day", delta_color="off")
    with o3:
        st.metric("Peak Single-Day Discharges", f"{max_daily:,}",
                  delta=df.loc[df['hhs_discharged'].idxmax(), 'date'].strftime("%b %d, %Y"),
                  delta_color="off")
    with o4:
        st.metric("Current Outcome Stability", f"{stab_now:.3f}",
                  delta="Target ≥ 0.70", delta_color="off")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Monthly Discharge Volume ───────────────────────────────────────────────
    st.markdown(
        "<div class='section-header'>MONTHLY DISCHARGE VOLUME</div>",
        unsafe_allow_html=True,
    )

    # Build monthly discharge chart
    fig_mo = go.Figure()

    # Bar for monthly totals
    fig_mo.add_trace(go.Bar(
        x=monthly["month_label"],
        y=monthly["hhs_discharged_sum"],
        marker_color=[
            COLORS["teal"] if v == monthly["hhs_discharged_sum"].max()
            else f"rgba(61,214,172,{0.4 + 0.5 * v / monthly['hhs_discharged_sum'].max()})"
            for v in monthly["hhs_discharged_sum"]
        ],
        marker_line_width=0,
        name="Monthly Discharges",
        hovertemplate="%{x}: <b>%{y:,} placements</b><extra></extra>",
    ))

    # 3-month rolling average line
    roll_avg = monthly["hhs_discharged_sum"].rolling(3, min_periods=1).mean()
    fig_mo.add_trace(go.Scatter(
        x=monthly["month_label"],
        y=roll_avg,
        line=dict(color=COLORS["orange"], width=2, dash="dot"),
        name="3-month MA",
        hovertemplate="%{x}: MA %{y:,.0f}<extra></extra>",
    ))

    # Highlight best month
    best_idx = monthly["hhs_discharged_sum"].idxmax()
    fig_mo.add_annotation(
        x=monthly.loc[best_idx, "month_label"],
        y=monthly.loc[best_idx, "hhs_discharged_sum"],
        text=f"Best: {monthly.loc[best_idx, 'hhs_discharged_sum']:,}",
        showarrow=True, arrowhead=2, arrowcolor=COLORS["teal"],
        font=dict(size=10, color=COLORS["teal"]),
        bgcolor="rgba(16,20,29,0.9)",
        bordercolor=COLORS["teal"], borderwidth=1,
    )

    fig_mo.update_layout(
        **dict(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Mono, monospace", color=COLORS["muted"], size=11),
            margin=dict(l=12, r=12, t=32, b=12),
            height=320,
            title=dict(text="Monthly Sponsor Placements (HHS Discharges)",
                       font=dict(size=13, color=COLORS["text"])),
            xaxis=dict(tickangle=-35, tickfont=dict(size=9),
                       gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(title="Placements", gridcolor="rgba(255,255,255,0.05)"),
            legend=dict(orientation="h", y=-0.2),
            barmode="overlay",
        )
    )
    st.plotly_chart(fig_mo, use_container_width=True, config={"displayModeBar": False})

    # ── Outcome Stability + Discharge Eff ─────────────────────────────────────
    st.markdown(
        "<div class='section-header' style='margin-top:4px'>OUTCOME CONSISTENCY ANALYSIS</div>",
        unsafe_allow_html=True,
    )

    oc1, oc2 = st.columns(2)
    with oc1:
        st.plotly_chart(
            outcome_stability_chart(df, height=280),
            use_container_width=True, config={"displayModeBar": False},
        )
    with oc2:
        st.plotly_chart(
            discharge_effectiveness_chart(monthly, height=280),
            use_container_width=True, config={"displayModeBar": False},
        )

    # ── Discharge Histogram ────────────────────────────────────────────────────
    st.markdown(
        "<div class='section-header' style='margin-top:4px'>DISCHARGE DISTRIBUTION</div>",
        unsafe_allow_html=True,
    )

    dh1, dh2 = st.columns([2, 1])
    with dh1:
        st.plotly_chart(
            discharge_histogram(df, height=260),
            use_container_width=True, config={"displayModeBar": False},
        )
    with dh2:
        # Distribution stats
        disc = df["hhs_discharged"].dropna()
        q1, q3 = disc.quantile(0.25), disc.quantile(0.75)
        st.markdown(
            f"""
            <div style="background:{COLORS['surface2']}; border:1px solid {COLORS['border']};
                        border-radius:8px; padding:16px; margin-top:8px">
              <div style="font-size:9px; letter-spacing:0.12em; text-transform:uppercase;
                          color:{COLORS['muted']}; margin-bottom:12px">
                Distribution Stats
              </div>
              {"".join([
                f'''<div style="display:flex; justify-content:space-between; padding:5px 0;
                    border-bottom:1px solid {COLORS['border']}">
                  <span style="font-size:10px; color:{COLORS['muted']}; font-family:'DM Mono',monospace">{label}</span>
                  <span style="font-size:11px; color:{COLORS['teal']}; font-family:'DM Mono',monospace; font-weight:500">{val}</span>
                </div>'''
                for label, val in [
                    ("Mean",   f"{disc.mean():.1f}/day"),
                    ("Median", f"{disc.median():.0f}/day"),
                    ("Std Dev",f"{disc.std():.1f}"),
                    ("Min",    f"{int(disc.min())}"),
                    ("Max",    f"{int(disc.max())}"),
                    ("Q1 (25%)",f"{q1:.0f}"),
                    ("Q3 (75%)",f"{q3:.0f}"),
                    ("IQR",    f"{q3 - q1:.0f}"),
                    ("CV",     f"{disc.std()/disc.mean()*100:.1f}%"),
                ]
              ])}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Year-over-Year Discharge Comparison ────────────────────────────────────
    st.markdown(
        "<div class='section-header' style='margin-top:16px'>YEAR-OVER-YEAR DISCHARGE COMPARISON</div>",
        unsafe_allow_html=True,
    )

    years = sorted(df["year"].unique().tolist())

    fig_yoy = go.Figure()
    year_colors = [COLORS["blue"], COLORS["orange"], COLORS["teal"]]

    for i, yr in enumerate(years):
        yr_df = df[df["year"] == yr].copy()
        # Use day-of-year for x axis
        yr_df["doy"] = yr_df["date"].dt.dayofyear
        # 7-day rolling average for smoothing
        yr_df = yr_df.sort_values("doy")
        yr_df["disc_ma"] = yr_df["hhs_discharged"].rolling(7, min_periods=1).mean()

        fig_yoy.add_trace(go.Scatter(
            x=yr_df["doy"],
            y=yr_df["disc_ma"],
            name=str(yr),
            line=dict(color=year_colors[i % len(year_colors)], width=2),
            mode="lines",
            hovertemplate=f"{yr} Day %{{x}}: <b>%{{y:.0f}}</b><extra></extra>",
        ))

    fig_yoy.update_layout(
        **dict(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Mono, monospace", color=COLORS["muted"], size=11),
            margin=dict(l=12, r=12, t=32, b=12),
            height=300,
            title=dict(text="Year-over-Year Daily Discharges (7-day MA, by Day of Year)",
                       font=dict(size=13, color=COLORS["text"])),
            xaxis=dict(title="Day of Year", gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(title="Daily Discharges (7d MA)", gridcolor="rgba(255,255,255,0.05)"),
            legend=dict(orientation="h", y=-0.2),
            hovermode="x unified",
        )
    )
    st.plotly_chart(fig_yoy, use_container_width=True, config={"displayModeBar": False})

    # Comparison table
    yoy_comparisons = []
    for j in range(len(years) - 1):
        comp = compare_periods(df, "hhs_discharged", str(years[j]), str(years[j+1]))
        yoy_comparisons.append({
            "Comparison":  f"{comp['period_a']} → {comp['period_b']}",
            "Avg Daily (A)":   f"{comp['mean_a']:.1f}",
            "Avg Daily (B)":   f"{comp['mean_b']:.1f}",
            "Change":     f"{comp['delta']:+.1f}",
            "% Change":   f"{comp['pct_change']:+.1f}%",
            "Direction":  comp["direction"].title(),
        })

    if yoy_comparisons:
        st.dataframe(pd.DataFrame(yoy_comparisons), use_container_width=True, hide_index=True)

    # ── Top 10 Discharge Months ───────────────────────────────────────────────
    with st.expander("🏆 Top 10 Best Discharge Months", expanded=False):
        top10 = (
            monthly[["month_label", "hhs_discharged_sum", "discharge_eff_avg",
                      "hhs_care_avg", "pipeline_status"]]
            .sort_values("hhs_discharged_sum", ascending=False)
            .head(10)
            .copy()
        )
        top10.columns = ["Month", "Total Discharges", "Avg Discharge Eff",
                         "Avg HHS Census", "Pipeline Status"]
        top10["Total Discharges"] = top10["Total Discharges"].astype(int)
        top10["Avg HHS Census"]   = top10["Avg HHS Census"].astype(int)
        top10["Avg Discharge Eff"]= (top10["Avg Discharge Eff"] * 100).round(3)
        st.dataframe(top10, use_container_width=True, hide_index=True)

    # ── Descriptive Statistics Table ──────────────────────────────────────────
    with st.expander("📊 Full Descriptive Statistics", expanded=False):
        cols_for_stats = [
            "cbp_apprehended", "cbp_custody", "cbp_transferred",
            "hhs_care", "hhs_discharged",
            "transfer_efficiency", "discharge_effectiveness", "pipeline_throughput",
        ]
        stats_df = summary_statistics(df, cols_for_stats)
        col_labels = {
            "cbp_apprehended":         "CBP Apprehended",
            "cbp_custody":             "CBP Custody",
            "cbp_transferred":         "CBP Transferred",
            "hhs_care":                "HHS Census",
            "hhs_discharged":          "HHS Discharged",
            "transfer_efficiency":     "Transfer Efficiency",
            "discharge_effectiveness": "Discharge Effectiveness",
            "pipeline_throughput":     "Pipeline Throughput",
        }
        stats_df.index = [col_labels.get(i, i) for i in stats_df.index]
        st.dataframe(stats_df, use_container_width=True)