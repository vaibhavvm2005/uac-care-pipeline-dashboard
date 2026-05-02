"""
charts.py
=========
Plotly chart factory functions for the UAC Care Pipeline Analytics dashboard.
Every function returns a go.Figure ready to pass to st.plotly_chart().
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import COLORS, PLOTLY_LAYOUT


def _base_layout(**overrides) -> dict:
    layout = dict(**PLOTLY_LAYOUT)
    layout.update(overrides)
    return layout


# ── 1. Pipeline Flow Bar (monthly overview) ──────────────────────────────────

def pipeline_flow_bar(df_monthly: pd.DataFrame, height: int = 300) -> go.Figure:
    """
    Grouped bar: monthly apprehensions, transfers, and discharges.
    """
    fig = go.Figure()
    series = [
        ("cbp_apprehended_sum", "CBP Apprehended", COLORS["orange"]),
        ("cbp_transferred_sum", "CBP → HHS Transfers", COLORS["blue"]),
        ("hhs_discharged_sum",  "HHS Discharges",   COLORS["teal"]),
    ]
    for col, name, color in series:
        fig.add_trace(go.Bar(
            x=df_monthly["month_label"],
            y=df_monthly[col],
            name=name,
            marker_color=color,
            marker_opacity=0.85,
            marker_line_width=0,
        ))
    fig.update_layout(
        **_base_layout(
            barmode="group",
            height=height,
            title=dict(text="Monthly Pipeline Volume", font=dict(size=13, color=COLORS["text"])),
            legend=dict(orientation="h", y=-0.18),
            xaxis=dict(tickangle=-35, tickfont=dict(size=9)),
        )
    )
    return fig


# ── 2. HHS Census Time Series ─────────────────────────────────────────────────

def hhs_census_chart(df: pd.DataFrame, height: int = 320) -> go.Figure:
    """
    Line chart of daily HHS Care census with MA and peak annotation.
    """
    peak_idx  = df["hhs_care"].idxmax()
    peak_date = df.loc[peak_idx, "date"]
    peak_val  = df.loc[peak_idx, "hhs_care"]

    fig = go.Figure()

    # Shaded fill under line
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["hhs_care"],
        fill="tozeroy",
        fillcolor=f"rgba(232,200,75,0.07)",
        line=dict(color=COLORS["yellow"], width=1.5),
        name="HHS Census",
        hovertemplate="%{x|%b %d %Y}: <b>%{y:,}</b><extra></extra>",
    ))

    # 30-day MA
    if "hhs_care_ma30d" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["hhs_care_ma30d"],
            line=dict(color=COLORS["orange"], width=2, dash="dot"),
            name="30-day MA",
            hovertemplate="%{x|%b %Y}: MA %{y:,.0f}<extra></extra>",
        ))

    # Peak annotation
    fig.add_annotation(
        x=peak_date, y=peak_val,
        text=f"Peak: {peak_val:,}",
        showarrow=True, arrowhead=2, arrowcolor=COLORS["red"],
        font=dict(size=10, color=COLORS["red"]),
        bgcolor="rgba(16,20,29,0.9)",
        bordercolor=COLORS["red"],
        borderwidth=1,
    )

    # Surge threshold reference line
    fig.add_hline(
        y=8000, line_dash="dash",
        line_color=f"rgba(240,79,79,0.4)",
        annotation_text="Surge Threshold (8,000)",
        annotation_position="top left",
        annotation_font_size=9,
        annotation_font_color=COLORS["danger"],
    )

    fig.update_layout(**_base_layout(
        height=height,
        title=dict(text="HHS Active Census Over Time", font=dict(size=13, color=COLORS["text"])),
        xaxis=dict(tickformat="%b %Y", tickangle=-30, tickfont=dict(size=9)),
        yaxis=dict(title="Children in Care"),
        showlegend=True,
    ))
    return fig


# ── 3. Transfer Efficiency Trend ──────────────────────────────────────────────

def transfer_efficiency_chart(df_monthly: pd.DataFrame, height: int = 280) -> go.Figure:
    """
    Line chart of monthly average transfer efficiency with target line.
    """
    vals = df_monthly["transfer_eff_avg"] * 100

    fig = go.Figure()

    # Area fill
    fig.add_trace(go.Scatter(
        x=df_monthly["month_label"], y=vals,
        fill="tozeroy",
        fillcolor=f"rgba(91,142,245,0.1)",
        line=dict(color=COLORS["blue"], width=2),
        mode="lines+markers",
        marker=dict(size=4, color=COLORS["blue"]),
        name="Transfer Efficiency %",
        hovertemplate="%{x}: <b>%{y:.1f}%</b><extra></extra>",
    ))

    # Target line at 75%
    fig.add_hline(
        y=75, line_dash="dash",
        line_color=f"rgba(61,214,172,0.5)",
        annotation_text="Target: 75%",
        annotation_position="top right",
        annotation_font_size=9,
        annotation_font_color=COLORS["teal"],
    )

    # Caution line at 55%
    fig.add_hline(
        y=55, line_dash="dot",
        line_color=f"rgba(232,200,75,0.3)",
        annotation_text="Caution: 55%",
        annotation_position="bottom right",
        annotation_font_size=9,
        annotation_font_color=COLORS["yellow"],
    )

    fig.update_layout(**_base_layout(
        height=height,
        title=dict(text="Transfer Efficiency Ratio (%)", font=dict(size=13, color=COLORS["text"])),
        xaxis=dict(tickangle=-35, tickfont=dict(size=9)),
        yaxis=dict(title="Efficiency %", ticksuffix="%"),
        showlegend=False,
    ))
    return fig


# ── 4. Discharge Effectiveness Trend ──────────────────────────────────────────

def discharge_effectiveness_chart(df_monthly: pd.DataFrame, height: int = 280) -> go.Figure:
    """
    Line chart of monthly discharge effectiveness index (%).
    """
    vals = df_monthly["discharge_eff_avg"] * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_monthly["month_label"], y=vals,
        fill="tozeroy",
        fillcolor=f"rgba(61,214,172,0.1)",
        line=dict(color=COLORS["teal"], width=2),
        mode="lines+markers",
        marker=dict(size=4, color=COLORS["teal"]),
        name="Discharge Effectiveness",
        hovertemplate="%{x}: <b>%{y:.2f}%</b><extra></extra>",
    ))

    fig.add_hline(
        y=3.0, line_dash="dash",
        line_color=f"rgba(61,214,172,0.4)",
        annotation_text="Target: 3.0%",
        annotation_font_size=9,
        annotation_font_color=COLORS["teal"],
    )

    fig.update_layout(**_base_layout(
        height=height,
        title=dict(text="Discharge Effectiveness Index (%)", font=dict(size=13, color=COLORS["text"])),
        xaxis=dict(tickangle=-35, tickfont=dict(size=9)),
        yaxis=dict(title="Daily Rate %", ticksuffix="%"),
        showlegend=False,
    ))
    return fig


# ── 5. Pipeline Throughput Bar ─────────────────────────────────────────────────

def throughput_bar_chart(df_monthly: pd.DataFrame, height: int = 280) -> go.Figure:
    """
    Bar chart coloured green/red based on throughput ≥1.0 or not.
    """
    vals   = df_monthly["throughput_avg"]
    colors = [COLORS["teal"] if v >= 1.0 else COLORS["red"] for v in vals]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_monthly["month_label"], y=vals,
        marker_color=colors,
        marker_line_width=0,
        name="Throughput",
        hovertemplate="%{x}: <b>%{y:.2f}x</b><extra></extra>",
    ))

    fig.add_hline(
        y=1.0, line_dash="dash",
        line_color=f"rgba(255,255,255,0.3)",
        annotation_text="Equilibrium (1.0×)",
        annotation_font_size=9,
        annotation_font_color=COLORS["muted"],
    )

    fig.update_layout(**_base_layout(
        height=height,
        title=dict(text="Pipeline Throughput Rate (×)", font=dict(size=13, color=COLORS["text"])),
        xaxis=dict(tickangle=-35, tickfont=dict(size=9)),
        yaxis=dict(title="Throughput ×"),
        showlegend=False,
    ))
    return fig


# ── 6. Backlog Area Chart ──────────────────────────────────────────────────────

def backlog_area_chart(df: pd.DataFrame, height: int = 320) -> go.Figure:
    """
    Stacked area chart: CBP Custody + HHS Care = Total Backlog.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["hhs_care"],
        name="HHS Care",
        stackgroup="backlog",
        fillcolor=f"rgba(232,200,75,0.45)",
        line=dict(color=COLORS["yellow"], width=0.5),
        hovertemplate="%{x|%b %d}: HHS %{y:,}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["cbp_custody"],
        name="CBP Custody",
        stackgroup="backlog",
        fillcolor=f"rgba(91,142,245,0.45)",
        line=dict(color=COLORS["blue"], width=0.5),
        hovertemplate="%{x|%b %d}: CBP %{y:,}<extra></extra>",
    ))

    # Peak backlog annotation
    peak_idx = df["system_backlog"].idxmax()
    fig.add_annotation(
        x=df.loc[peak_idx, "date"],
        y=df.loc[peak_idx, "system_backlog"],
        text=f"Peak Backlog<br>{df.loc[peak_idx, 'system_backlog']:,}",
        showarrow=True, arrowhead=2, arrowcolor=COLORS["red"],
        font=dict(size=9, color=COLORS["red"]),
        bgcolor="rgba(16,20,29,0.9)",
        bordercolor=COLORS["red"],
        borderwidth=1,
    )

    fig.update_layout(**_base_layout(
        height=height,
        title=dict(text="System Backlog — CBP + HHS Combined", font=dict(size=13, color=COLORS["text"])),
        xaxis=dict(tickformat="%b %Y", tickangle=-30, tickfont=dict(size=9)),
        yaxis=dict(title="Children in System"),
        legend=dict(orientation="h", y=-0.2),
        hovermode="x unified",
    ))
    return fig


# ── 7. Net Flow Bar ────────────────────────────────────────────────────────────

def net_flow_chart(df_monthly: pd.DataFrame, height: int = 280) -> go.Figure:
    """
    Bar chart of monthly net flow (Transfers − Discharges).
    Red = backlog growing, teal = backlog clearing.
    """
    net = df_monthly["cbp_transferred_sum"] - df_monthly["hhs_discharged_sum"]
    colors = [COLORS["red"] if v > 0 else COLORS["teal"] for v in net]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_monthly["month_label"], y=net,
        marker_color=colors,
        marker_line_width=0,
        name="Net Flow",
        hovertemplate="%{x}: <b>%{y:+,.0f}</b><extra></extra>",
    ))

    fig.add_hline(y=0, line_color="rgba(255,255,255,0.2)", line_width=1)

    fig.update_layout(**_base_layout(
        height=height,
        title=dict(text="Monthly Net Flow (Transfers − Discharges)", font=dict(size=13, color=COLORS["text"])),
        xaxis=dict(tickangle=-35, tickfont=dict(size=9)),
        yaxis=dict(title="Net Children"),
        showlegend=False,
    ))
    return fig


# ── 8. Weekday Performance Heatmap ────────────────────────────────────────────

def weekday_heatmap(df_weekday: pd.DataFrame, height: int = 220) -> go.Figure:
    """
    Horizontal bar chart of average daily discharges by weekday.
    """
    order  = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    df_wk  = df_weekday.set_index("weekday").reindex(order).reset_index()
    vals   = df_wk["avg_discharged"].fillna(0)
    max_v  = vals.max()
    colors = [
        f"rgba(61,214,172,{0.3 + 0.65 * (v / max_v) if max_v else 0.3})"
        for v in vals
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_wk["weekday"], y=vals,
        marker_color=colors,
        marker_line_width=0,
        text=vals.round(0).astype(int),
        textposition="outside",
        textfont=dict(size=10, color=COLORS["text"]),
        hovertemplate="%{x}: <b>%{y:.1f} avg discharges</b><extra></extra>",
    ))

    fig.update_layout(**_base_layout(
        height=height,
        title=dict(text="Avg Daily Discharges by Weekday", font=dict(size=13, color=COLORS["text"])),
        yaxis=dict(title="Avg Discharges"),
        showlegend=False,
    ))
    return fig


# ── 9. Outcome Stability Line ─────────────────────────────────────────────────

def outcome_stability_chart(df: pd.DataFrame, height: int = 280) -> go.Figure:
    """
    Rolling 30-day outcome stability score over time.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["outcome_stability"],
        fill="tozeroy",
        fillcolor="rgba(91,142,245,0.08)",
        line=dict(color=COLORS["blue"], width=1.5),
        name="Stability Score",
        hovertemplate="%{x|%b %d %Y}: <b>%{y:.3f}</b><extra></extra>",
    ))

    fig.add_hline(
        y=0.70, line_dash="dash",
        line_color=f"rgba(61,214,172,0.4)",
        annotation_text="Target: 0.70",
        annotation_font_size=9,
        annotation_font_color=COLORS["teal"],
    )

    fig.update_layout(**_base_layout(
        height=height,
        title=dict(text="Outcome Stability Score (30-day rolling)", font=dict(size=13, color=COLORS["text"])),
        xaxis=dict(tickformat="%b %Y", tickangle=-30, tickfont=dict(size=9)),
        yaxis=dict(title="Stability Score", range=[0, 1.05]),
        showlegend=False,
    ))
    return fig


# ── 10. KPI Gauge ──────────────────────────────────────────────────────────────

def kpi_gauge(value: float, title: str, min_val: float = 0,
              max_val: float = 1, target: float = 0.75,
              height: int = 180, suffix: str = "") -> go.Figure:
    """
    Bullet-style gauge for a single KPI.
    """
    # Determine color
    pct = value / max_val if max_val else 0
    color = COLORS["teal"] if pct >= 0.75 else COLORS["yellow"] if pct >= 0.55 else COLORS["red"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        number=dict(suffix=suffix, font=dict(size=28, color=color, family="Syne, sans-serif")),
        delta=dict(reference=target, suffix=suffix, font=dict(size=12)),
        gauge=dict(
            axis=dict(range=[min_val, max_val], tickcolor=COLORS["muted"],
                      tickfont=dict(size=9)),
            bar=dict(color=color, thickness=0.6),
            bgcolor="rgba(22,27,39,0.8)",
            borderwidth=0,
            steps=[
                dict(range=[min_val, target * 0.73], color="rgba(240,79,79,0.15)"),
                dict(range=[target * 0.73, target],  color="rgba(232,200,75,0.15)"),
                dict(range=[target, max_val],         color="rgba(61,214,172,0.10)"),
            ],
            threshold=dict(
                line=dict(color=COLORS["teal"], width=2),
                thickness=0.8,
                value=target,
            ),
        ),
        title=dict(text=title, font=dict(size=11, color=COLORS["muted"])),
    ))

    fig.update_layout(**_base_layout(
        height=height,
        margin=dict(l=20, r=20, t=40, b=10),
    ))
    return fig


# ── 11. Correlation Heatmap ────────────────────────────────────────────────────

def correlation_heatmap(df: pd.DataFrame, height: int = 320) -> go.Figure:
    """
    Correlation heatmap of key pipeline metrics.
    """
    cols = {
        "cbp_apprehended": "CBP Apprehended",
        "cbp_custody":     "CBP Custody",
        "cbp_transferred": "CBP Transferred",
        "hhs_care":        "HHS Census",
        "hhs_discharged":  "HHS Discharged",
        "transfer_efficiency":    "Transfer Eff",
        "discharge_effectiveness":"Discharge Eff",
    }
    sub = df[[c for c in cols if c in df.columns]].rename(columns=cols)
    corr = sub.corr().round(2)

    fig = go.Figure(go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        colorscale=[
            [0.0, COLORS["red"]],
            [0.5, COLORS["surface2"]],
            [1.0, COLORS["teal"]],
        ],
        zmin=-1, zmax=1,
        text=corr.values.round(2),
        texttemplate="%{text}",
        textfont=dict(size=10),
        showscale=True,
        colorbar=dict(thickness=12, tickfont=dict(size=9)),
    ))

    fig.update_layout(**_base_layout(
        height=height,
        title=dict(text="Metric Correlation Matrix", font=dict(size=13, color=COLORS["text"])),
        xaxis=dict(tickangle=-30, tickfont=dict(size=9)),
        yaxis=dict(tickfont=dict(size=9)),
    ))
    return fig


# ── 12. Daily Discharge Distribution (histogram) ──────────────────────────────

def discharge_histogram(df: pd.DataFrame, height: int = 260) -> go.Figure:
    """
    Histogram of daily discharge counts to show distribution shape.
    """
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=df["hhs_discharged"].dropna(),
        nbinsx=40,
        marker_color=COLORS["teal"],
        marker_opacity=0.8,
        marker_line_width=0,
        name="Daily Discharges",
        hovertemplate="Range: %{x}<br>Days: %{y}<extra></extra>",
    ))

    mean_val = df["hhs_discharged"].mean()
    fig.add_vline(
        x=mean_val, line_dash="dash",
        line_color=COLORS["orange"],
        annotation_text=f"Mean: {mean_val:.0f}",
        annotation_font_size=9,
        annotation_font_color=COLORS["orange"],
    )

    fig.update_layout(**_base_layout(
        height=height,
        title=dict(text="Distribution of Daily Discharges", font=dict(size=13, color=COLORS["text"])),
        xaxis=dict(title="Daily Discharges"),
        yaxis=dict(title="Number of Days"),
        showlegend=False,
    ))
    return fig