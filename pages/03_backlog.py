"""
p03_backlog.py
==============
Page 3: Backlog Detection & Net Flow Analysis
- System backlog stacked area
- Net flow monthly bar
- Bottleneck period detection table
- Backlog accumulation rate
- Daily backlog delta
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import COLORS
from utils.data_loader import load_processed, monthly_summary, system_kpis
from utils.metrics import detect_bottleneck_periods, identify_stagnation_periods
from utils.charts import backlog_area_chart, net_flow_chart


def render():
    st.markdown(
        f"""
        <div style="margin-bottom:24px">
          <div style="font-family:Syne,sans-serif; font-weight:800; font-size:22px;
                      color:{COLORS['text']}; letter-spacing:-0.01em">
            Backlog Detection
          </div>
          <div style="font-size:11px; color:{COLORS['muted']}; margin-top:4px;
                      font-family:'DM Mono',monospace">
            Identifying where and when the care pipeline accumulates unresolved cases
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df      = load_processed()
    monthly = monthly_summary()
    kpis    = system_kpis()

    # ── Summary Metrics ───────────────────────────────────────────────────────
    st.markdown(
        "<div class='section-header'>BACKLOG STATUS SUMMARY</div>",
        unsafe_allow_html=True,
    )

    b1, b2, b3, b4 = st.columns(4)
    peak_bl   = int(df["system_backlog"].max())
    curr_bl   = int(df["system_backlog"].iloc[-1])
    peak_bl_d = df.loc[df["system_backlog"].idxmax(), "date"].strftime("%b %d, %Y")
    trend_7d  = df["system_backlog"].tail(7).diff().mean()

    with b1:
        st.metric("Peak System Backlog", f"{peak_bl:,}", delta=peak_bl_d, delta_color="off")
    with b2:
        st.metric("Current Backlog", f"{curr_bl:,}",
                  delta=f"{((curr_bl - peak_bl) / peak_bl * 100):.1f}% from peak",
                  delta_color="inverse")
    with b3:
        st.metric("7-Day Backlog Trend",
                  f"{'↑' if trend_7d > 0 else '↓'} {abs(trend_7d):.1f}/day",
                  delta="Growing" if trend_7d > 0 else "Clearing",
                  delta_color="inverse" if trend_7d > 0 else "normal")
    with b4:
        net_sum_recent = df["net_flow_hhs"].tail(30).sum()
        st.metric("30-Day Net Flow", f"{net_sum_recent:+,.0f}",
                  delta="Inflow surplus" if net_sum_recent > 0 else "Outflow surplus",
                  delta_color="inverse" if net_sum_recent > 0 else "normal")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Backlog Chart ─────────────────────────────────────────────────────────
    st.markdown(
        "<div class='section-header'>SYSTEM BACKLOG — CBP + HHS COMBINED</div>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        backlog_area_chart(df, height=340),
        use_container_width=True, config={"displayModeBar": False},
    )

    # ── Net Flow ──────────────────────────────────────────────────────────────
    st.markdown(
        "<div class='section-header' style='margin-top:4px'>MONTHLY NET FLOW (TRANSFERS − DISCHARGES)</div>",
        unsafe_allow_html=True,
    )

    col_note, col_chart = st.columns([1, 3])
    with col_note:
        st.markdown(
            f"""
            <div style="background:{COLORS['surface2']}; border:1px solid {COLORS['border']};
                        border-radius:8px; padding:14px; margin-top:8px">
              <div style="font-size:9px; letter-spacing:0.1em; text-transform:uppercase;
                          color:{COLORS['muted']}; margin-bottom:10px">How to Read</div>
              <div style="font-size:11px; color:{COLORS['text']}; line-height:1.6;
                          font-family:'DM Mono',monospace">
                <span style="color:{COLORS['red']}">■</span> Red bars = more transfers in
                than discharges out → backlog growing<br><br>
                <span style="color:{COLORS['teal']}">■</span> Teal bars = more discharges
                out → backlog clearing<br><br>
                The zero line = equilibrium (system in balance)
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_chart:
        st.plotly_chart(
            net_flow_chart(monthly, height=280),
            use_container_width=True, config={"displayModeBar": False},
        )

    # ── Bottleneck Detection ──────────────────────────────────────────────────
    st.markdown(
        "<div class='section-header' style='margin-top:16px'>BOTTLENECK PERIOD DETECTION</div>",
        unsafe_allow_html=True,
    )

    min_days = st.slider(
        "Minimum consecutive days for bottleneck classification",
        min_value=5, max_value=30, value=14, step=1,
    )

    bottlenecks = detect_bottleneck_periods(df, consecutive_days=min_days)

    if len(bottlenecks) > 0:
        st.markdown(
            f"""
            <div style="background:rgba(240,79,79,0.08); border:1px solid rgba(240,79,79,0.2);
                        border-radius:8px; padding:12px 16px; margin-bottom:12px;
                        font-size:11px; color:{COLORS['text']}; font-family:'DM Mono',monospace">
              ⚠️ Detected <strong style="color:{COLORS['red']}">{len(bottlenecks)} bottleneck periods</strong>
              where net flow was positive for ≥{min_days} consecutive days.
            </div>
            """,
            unsafe_allow_html=True,
        )

        display_bt = bottlenecks.copy()
        display_bt["start_date"] = display_bt["start_date"].dt.strftime("%Y-%m-%d")
        display_bt["end_date"]   = display_bt["end_date"].dt.strftime("%Y-%m-%d")
        display_bt.columns       = ["Start Date", "End Date", "Duration (days)",
                                    "Peak Backlog", "Total Net Inflow"]
        display_bt["Peak Backlog"]     = display_bt["Peak Backlog"].astype(int)
        display_bt["Total Net Inflow"] = display_bt["Total Net Inflow"].astype(int)

        st.dataframe(display_bt, use_container_width=True, hide_index=True)
    else:
        st.success(f"✅ No bottleneck periods detected with ≥{min_days} consecutive days of positive net flow.")

    # ── Stagnation Detection ──────────────────────────────────────────────────
    st.markdown(
        "<div class='section-header' style='margin-top:16px'>DISCHARGE STAGNATION DETECTION</div>",
        unsafe_allow_html=True,
    )

    stag = identify_stagnation_periods(df, threshold=0.01, window=14)

    if len(stag) > 0:
        st.markdown(
            f"""
            <div style="background:rgba(232,200,75,0.08); border:1px solid rgba(232,200,75,0.2);
                        border-radius:8px; padding:12px 16px; margin-bottom:12px;
                        font-size:11px; color:{COLORS['text']}; font-family:'DM Mono',monospace">
              🟡 Detected <strong style="color:{COLORS['yellow']}">{len(stag)} stagnation periods</strong>
              where discharge effectiveness fell below 1.0% for ≥14 days.
            </div>
            """,
            unsafe_allow_html=True,
        )
        display_stag = stag.copy()
        display_stag["start_date"] = display_stag["start_date"].dt.strftime("%Y-%m-%d")
        display_stag["end_date"]   = display_stag["end_date"].dt.strftime("%Y-%m-%d")
        display_stag["avg_discharge_eff"] = (display_stag["avg_discharge_eff"] * 100).round(3)
        display_stag.columns = ["Start Date", "End Date", "Duration (days)", "Avg Discharge Eff (%)"]
        st.dataframe(display_stag, use_container_width=True, hide_index=True)
    else:
        st.success("✅ No significant discharge stagnation periods detected.")

    # ── Backlog Delta Distribution ────────────────────────────────────────────
    with st.expander("📊 Daily Backlog Delta Distribution", expanded=False):
        delta = df["backlog_delta"].dropna()
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=delta,
            nbinsx=50,
            marker_color=[COLORS["red"] if v > 0 else COLORS["teal"]
                          for v in delta],
            marker_line_width=0,
            name="Backlog Delta",
        ))
        fig.add_vline(x=0, line_dash="dash", line_color=COLORS["muted"])
        fig.update_layout(
            **dict(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="DM Mono, monospace", color=COLORS["muted"], size=11),
                margin=dict(l=12, r=12, t=32, b=12),
                height=260,
                title=dict(text="Distribution of Daily Backlog Changes",
                           font=dict(size=13, color=COLORS["text"])),
                xaxis=dict(title="Daily Change", gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(title="Number of Days", gridcolor="rgba(255,255,255,0.05)"),
                showlegend=False,
            )
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        negative_days = (delta < 0).sum()
        positive_days = (delta > 0).sum()
        st.markdown(
            f"""
            <div style="font-size:10px; color:{COLORS['muted']}; font-family:'DM Mono',monospace; padding:6px 0">
              Backlog shrinking days: <strong style="color:{COLORS['teal']}">{negative_days}</strong> &nbsp;|&nbsp;
              Backlog growing days: <strong style="color:{COLORS['red']}">{positive_days}</strong> &nbsp;|&nbsp;
              Mean daily change: <strong style="color:{COLORS['text']}">{delta.mean():+.1f}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )