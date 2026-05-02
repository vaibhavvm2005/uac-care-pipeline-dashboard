"""
p05_report.py
=============
Page 5: Monthly Performance Report
- Filterable monthly performance table
- All KPIs per month with colour-coded status
- Excel download button
- Plain-text executive summary download
- Threshold alert summary
"""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import COLORS, THRESHOLDS
from utils.data_loader import load_processed, monthly_summary, system_kpis
from utils.metrics import get_status
from utils.export import build_excel_report, build_text_summary


def _status_badge(label: str, color: str) -> str:
    alpha = "0.15"
    return (
        f'<span style="background:rgba({_hex_to_rgb(color)},{alpha}); '
        f'color:{color}; border:1px solid {color}; border-radius:3px; '
        f'padding:1px 6px; font-size:9px; font-family:\'DM Mono\',monospace; '
        f'letter-spacing:0.06em">{label}</span>'
    )


def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b}"


def render():
    st.markdown(
        f"""
        <div style="margin-bottom:24px">
          <div style="font-family:Syne,sans-serif; font-weight:800; font-size:22px;
                      color:{COLORS['text']}; letter-spacing:-0.01em">
            Monthly Performance Report
          </div>
          <div style="font-size:11px; color:{COLORS['muted']}; margin-top:4px;
                      font-family:'DM Mono',monospace">
            Filterable pipeline performance table · Export to Excel &amp; Text
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df      = load_processed()
    monthly = monthly_summary()
    kpis    = system_kpis()

    # ── Filters ───────────────────────────────────────────────────────────────
    st.markdown(
        "<div class='section-header'>FILTERS &amp; EXPORT</div>",
        unsafe_allow_html=True,
    )

    fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 2])

    with fc1:
        all_years = sorted(monthly["year"].unique().tolist())
        sel_years = st.multiselect(
            "Filter by Year",
            options=all_years,
            default=all_years,
            key="report_year",
        )

    with fc2:
        status_options = ["All", "High Throughput", "Balanced", "Backlog Risk"]
        sel_status = st.selectbox("Pipeline Status", options=status_options, key="report_status")

    with fc3:
        sort_col = st.selectbox(
            "Sort by",
            options=["Month (default)", "Transfer Eff %", "Discharge Eff %",
                     "HHS Discharges", "Throughput", "Avg HHS Census"],
            key="report_sort",
        )

    with fc4:
        sort_asc = st.radio("Sort direction", ["Descending", "Ascending"],
                            horizontal=True, key="report_asc")

    # Apply filters
    filtered = monthly[monthly["year"].isin(sel_years)].copy()
    if sel_status != "All":
        filtered = filtered[filtered["pipeline_status"] == sel_status]

    # Sort
    sort_map = {
        "Month (default)":   ("month_str", True),
        "Transfer Eff %":    ("transfer_eff_avg", False),
        "Discharge Eff %":   ("discharge_eff_avg", False),
        "HHS Discharges":    ("hhs_discharged_sum", False),
        "Throughput":        ("throughput_avg", False),
        "Avg HHS Census":    ("hhs_care_avg", False),
    }
    sort_field, default_asc = sort_map[sort_col]
    ascending = (sort_asc == "Ascending")
    filtered = filtered.sort_values(sort_field, ascending=ascending)

    st.markdown(
        f"""
        <div style="font-size:10px; color:{COLORS['muted']}; font-family:'DM Mono',monospace;
                    margin-bottom:12px">
          Showing <strong style="color:{COLORS['teal']}">{len(filtered)}</strong> months
          | Total discharges in view:
          <strong style="color:{COLORS['teal']}">{int(filtered['hhs_discharged_sum'].sum()):,}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Export Buttons ─────────────────────────────────────────────────────────
    ex1, ex2, ex3 = st.columns([2, 2, 4])

    with ex1:
        try:
            excel_bytes = build_excel_report(df, monthly)
            st.download_button(
                label="⬇️  Download Excel Report",
                data=excel_bytes,
                file_name="UAC_Pipeline_Analytics_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"Excel export unavailable: {e}")

    with ex2:
        txt_summary = build_text_summary(df, monthly)
        st.download_button(
            label="📄  Download Text Summary",
            data=txt_summary,
            file_name="UAC_Executive_Summary.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Performance Table ──────────────────────────────────────────────────────
    st.markdown(
        "<div class='section-header'>MONTHLY PERFORMANCE TABLE</div>",
        unsafe_allow_html=True,
    )

    # Build display DataFrame
    display = filtered[[
        "month_label",
        "reporting_days",
        "cbp_apprehended_sum",
        "cbp_transferred_sum",
        "hhs_discharged_sum",
        "hhs_care_avg",
        "hhs_care_max",
        "cbp_custody_avg",
        "transfer_eff_avg",
        "discharge_eff_avg",
        "throughput_avg",
        "net_flow_sum",
        "pipeline_status",
    ]].copy()

    display["transfer_eff_pct"]  = (display["transfer_eff_avg"] * 100).round(1)
    display["discharge_eff_pct"] = (display["discharge_eff_avg"] * 100).round(3)
    display["throughput_fmt"]    = display["throughput_avg"].round(3)
    display["hhs_care_avg"]      = display["hhs_care_avg"].round(0).astype(int)
    display["hhs_care_max"]      = display["hhs_care_max"].astype(int)
    display["net_flow_sum"]      = display["net_flow_sum"].astype(int)

    display = display[[
        "month_label", "reporting_days",
        "cbp_apprehended_sum", "cbp_transferred_sum", "hhs_discharged_sum",
        "hhs_care_avg", "hhs_care_max",
        "transfer_eff_pct", "discharge_eff_pct", "throughput_fmt",
        "net_flow_sum", "pipeline_status",
    ]]

    display.columns = [
        "Month", "Days",
        "CBP Apprehended", "CBP Transferred", "HHS Discharged",
        "Avg HHS Census", "Peak HHS Census",
        "Transfer Eff %", "Discharge Eff %", "Throughput ×",
        "Net Flow", "Status",
    ]

    # Style the dataframe with conditional formatting
    def style_table(df_style):
        styles = pd.DataFrame("", index=df_style.index, columns=df_style.columns)

        # Transfer Efficiency colouring
        if "Transfer Eff %" in df_style.columns:
            for idx in df_style.index:
                val = df_style.loc[idx, "Transfer Eff %"]
                if pd.notna(val):
                    if val >= 75:
                        styles.loc[idx, "Transfer Eff %"] = "color: #3dd6ac; font-weight: 500"
                    elif val >= 55:
                        styles.loc[idx, "Transfer Eff %"] = "color: #e8c84b"
                    else:
                        styles.loc[idx, "Transfer Eff %"] = "color: #f04f4f"

        # Throughput colouring
        if "Throughput ×" in df_style.columns:
            for idx in df_style.index:
                val = df_style.loc[idx, "Throughput ×"]
                if pd.notna(val):
                    if val >= 1.3:
                        styles.loc[idx, "Throughput ×"] = "color: #3dd6ac; font-weight: 500"
                    elif val >= 0.9:
                        styles.loc[idx, "Throughput ×"] = "color: #e8c84b"
                    else:
                        styles.loc[idx, "Throughput ×"] = "color: #f04f4f"

        # Net Flow colouring
        if "Net Flow" in df_style.columns:
            for idx in df_style.index:
                val = df_style.loc[idx, "Net Flow"]
                if pd.notna(val):
                    if val < 0:
                        styles.loc[idx, "Net Flow"] = "color: #3dd6ac"
                    else:
                        styles.loc[idx, "Net Flow"] = "color: #f04f4f"

        return styles

    styled = display.style.apply(style_table, axis=None)
    st.dataframe(styled, use_container_width=True, hide_index=True, height=520)

    # ── Threshold Alert Log ────────────────────────────────────────────────────
    st.markdown(
        "<div class='section-header' style='margin-top:20px'>THRESHOLD ALERT LOG</div>",
        unsafe_allow_html=True,
    )

    alert_rows = []
    for _, row in filtered.iterrows():
        te  = row["transfer_eff_avg"]
        de  = row["discharge_eff_avg"]
        thr = row["throughput_avg"]
        cen = row["hhs_care_avg"]

        te_s  = get_status("transfer_eff",    te)
        de_s  = get_status("discharge_eff",   de)
        thr_s = get_status("throughput",      thr)
        cen_s = get_status("hhs_census",      cen)

        # Only include months with at least one non-green status
        alerts_in_row = [
            (k, s) for k, s in [
                ("Transfer Eff",    te_s),
                ("Discharge Eff",   de_s),
                ("Throughput",      thr_s),
                ("HHS Census",      cen_s),
            ]
            if s["label"] != "Good" and s["label"] != "Normal"
        ]

        if alerts_in_row:
            alert_rows.append({
                "Month":   row["month_label"],
                "Alerts":  ", ".join(f"{k}: {s['emoji']} {s['label']}" for k, s in alerts_in_row),
                "HHS Avg": f"{int(row['hhs_care_avg']):,}",
                "Transfer Eff %": f"{te * 100:.1f}%",
                "Throughput ×":   f"{thr:.2f}",
            })

    if alert_rows:
        st.markdown(
            f"""
            <div style="background:rgba(240,79,79,0.05); border:1px solid rgba(240,79,79,0.15);
                        border-radius:8px; padding:10px 14px; margin-bottom:12px;
                        font-size:10px; color:{COLORS['muted']}; font-family:'DM Mono',monospace">
              ⚠️ <strong style="color:{COLORS['text']}">{len(alert_rows)}</strong> months
              with at least one KPI below target threshold.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(pd.DataFrame(alert_rows), use_container_width=True, hide_index=True)
    else:
        st.success("✅ All filtered months meet KPI targets.")

    # ── Executive Summary Box ──────────────────────────────────────────────────
    with st.expander("📋 Inline Executive Summary", expanded=False):
        st.code(build_text_summary(df, monthly), language=None)

    # ── Pivot: Monthly Metrics Heatmap View ───────────────────────────────────
    with st.expander("🗂️ Transfer Efficiency Heatmap by Month × Year", expanded=False):
        pivot_data = monthly.copy()
        pivot_data["month_num"] = pd.to_datetime(pivot_data["month_str"]).dt.strftime("%b")
        pivot_data["te_pct"]    = (pivot_data["transfer_eff_avg"] * 100).round(1)

        try:
            pivot = pivot_data.pivot_table(
                index="year", columns="month_num", values="te_pct", aggfunc="mean"
            )
            # Reorder month columns
            month_order = ["Jan","Feb","Mar","Apr","May","Jun",
                           "Jul","Aug","Sep","Oct","Nov","Dec"]
            pivot = pivot.reindex(columns=[m for m in month_order if m in pivot.columns])

            import plotly.graph_objects as go
            fig_hm = go.Figure(go.Heatmap(
                z=pivot.values,
                x=pivot.columns.tolist(),
                y=pivot.index.tolist(),
                colorscale=[
                    [0.0,  COLORS["red"]],
                    [0.55, COLORS["yellow"]],
                    [1.0,  COLORS["teal"]],
                ],
                zmin=0, zmax=100,
                text=pivot.values.round(1),
                texttemplate="%{text}%",
                textfont=dict(size=10),
                showscale=True,
                colorbar=dict(
                    title="Eff %",
                    thickness=12,
                    tickfont=dict(size=9),
                ),
                hovertemplate="Year %{y} — %{x}: <b>%{z:.1f}%</b><extra></extra>",
            ))

            fig_hm.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="DM Mono, monospace", color=COLORS["muted"], size=11),
                margin=dict(l=12, r=12, t=40, b=12),
                height=220,
                title=dict(text="Transfer Efficiency % — Year × Month Heatmap",
                           font=dict(size=13, color=COLORS["text"])),
            )
            st.plotly_chart(fig_hm, use_container_width=True, config={"displayModeBar": False})
        except Exception as e:
            st.info(f"Heatmap unavailable: {e}")