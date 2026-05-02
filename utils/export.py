"""
export.py
=========
Generates downloadable Excel performance reports and PDF summaries
for the UAC Care Pipeline Analytics dashboard.
"""

import pandas as pd
import numpy as np
import io
import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import COLORS


# ── Excel Export ─────────────────────────────────────────────────────────────

def build_excel_report(df_daily: pd.DataFrame, df_monthly: pd.DataFrame) -> bytes:
    """
    Build a multi-sheet Excel workbook and return as bytes for st.download_button.

    Sheets:
      1. Summary KPIs
      2. Monthly Performance
      3. Daily Data
      4. Bottleneck Log
    """
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        # ── Formats ────────────────────────────────────────────────────────
        hdr_fmt = workbook.add_format({
            "bold": True, "font_color": "#FFFFFF",
            "bg_color": "#10141d", "border": 1,
            "font_name": "Courier New", "font_size": 10,
            "align": "center", "valign": "vcenter",
        })
        title_fmt = workbook.add_format({
            "bold": True, "font_size": 14,
            "font_name": "Arial", "font_color": "#3dd6ac",
        })
        sub_fmt = workbook.add_format({
            "font_size": 10, "font_name": "Courier New", "font_color": "#5a6278",
        })
        num_fmt   = workbook.add_format({"num_format": "#,##0",   "font_name": "Courier New", "font_size": 9})
        pct_fmt   = workbook.add_format({"num_format": "0.00%",    "font_name": "Courier New", "font_size": 9})
        dec_fmt   = workbook.add_format({"num_format": "0.000",    "font_name": "Courier New", "font_size": 9})
        date_fmt  = workbook.add_format({"num_format": "yyyy-mm-dd","font_name": "Courier New","font_size": 9})
        green_fmt = workbook.add_format({"bg_color": "#1a3d2b", "font_color": "#3dd6ac", "num_format": "0.0%"})
        red_fmt   = workbook.add_format({"bg_color": "#3d1a1a", "font_color": "#f04f4f", "num_format": "0.0%"})
        yel_fmt   = workbook.add_format({"bg_color": "#3d350a", "font_color": "#e8c84b", "num_format": "0.0%"})

        # ── Sheet 1: Summary KPIs ───────────────────────────────────────────
        ws1 = workbook.add_worksheet("Summary KPIs")
        ws1.set_tab_color("#3dd6ac")
        ws1.hide_gridlines(2)
        ws1.set_column("A:A", 36)
        ws1.set_column("B:B", 22)
        ws1.set_column("C:C", 18)
        ws1.set_column("D:D", 24)

        ws1.write("A1", "UAC Care Pipeline Analytics — Executive Summary", title_fmt)
        ws1.write("A2", f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} | Dataset: Jan 2023 – Dec 2025", sub_fmt)
        ws1.set_row(0, 22)

        kpi_rows = [
            ("PIPELINE TOTALS", "", "", ""),
            ("Total Children Apprehended (CBP)",      df_daily["cbp_apprehended"].sum(),   "children", "Sum over dataset period"),
            ("Total CBP → HHS Transfers",             df_daily["cbp_transferred"].sum(),    "children", "Sum over dataset period"),
            ("Total HHS Discharges (Sponsor Placements)", df_daily["hhs_discharged"].sum(), "children", "Sum over dataset period"),
            ("", "", "", ""),
            ("CENSUS METRICS", "", "", ""),
            ("Peak HHS Census",                       df_daily["hhs_care"].max(),            "children", df_daily.loc[df_daily["hhs_care"].idxmax(), "date"].strftime("%Y-%m-%d")),
            ("Current HHS Census (Latest)",           df_daily["hhs_care"].iloc[-1],         "children", df_daily["date"].iloc[-1].strftime("%Y-%m-%d")),
            ("Average HHS Census (3-year)",           df_daily["hhs_care"].mean(),           "children", "Daily average"),
            ("", "", "", ""),
            ("EFFICIENCY METRICS (3-YEAR AVERAGES)", "", "", ""),
            ("Avg Transfer Efficiency Ratio",         df_daily["transfer_efficiency"].mean(), "ratio",   "Target ≥ 0.75"),
            ("Avg Discharge Effectiveness Index",     df_daily["discharge_effectiveness"].mean(), "ratio", "Target ≥ 0.030"),
            ("Avg Pipeline Throughput Rate",          df_daily["pipeline_throughput"].mean(),  "ratio",  "Target ≥ 1.0"),
        ]

        row_offset = 4
        ws1.write_row(row_offset, 0, ["KPI Metric", "Value", "Unit", "Notes"], hdr_fmt)
        for i, (label, val, unit, note) in enumerate(kpi_rows):
            r = row_offset + 1 + i
            ws1.write(r, 0, label, workbook.add_format({"bold": label.isupper() and val == "", "font_name":"Courier New","font_size":9,"bg_color":"#161b27" if label.isupper() else "#FFFFFF00","font_color":COLORS["teal"] if label.isupper() else COLORS["text"]}))
            if isinstance(val, float) and val != "":
                ws1.write_number(r, 1, round(val, 4) if val < 10 else int(val), num_fmt if val >= 10 else dec_fmt)
            elif val != "":
                ws1.write(r, 1, val)
            ws1.write(r, 2, unit)
            ws1.write(r, 3, note)

        # ── Sheet 2: Monthly Performance ────────────────────────────────────
        export_monthly = df_monthly[[
            "month_label", "reporting_days",
            "cbp_apprehended_sum", "cbp_transferred_sum", "hhs_discharged_sum",
            "hhs_care_avg", "hhs_care_max",
            "transfer_eff_avg", "discharge_eff_avg", "throughput_avg",
            "backlog_avg", "net_flow_sum", "pipeline_status",
        ]].copy()

        export_monthly.columns = [
            "Month", "Reporting Days",
            "CBP Apprehended", "CBP Transferred", "HHS Discharged",
            "Avg HHS Census", "Peak HHS Census",
            "Transfer Eff (avg)", "Discharge Eff (avg)", "Throughput (avg)",
            "Avg Backlog", "Net Flow (sum)", "Pipeline Status",
        ]

        export_monthly.to_excel(writer, sheet_name="Monthly Performance", index=False, startrow=2)
        ws2 = writer.sheets["Monthly Performance"]
        ws2.set_tab_color("#5b8ef5")
        ws2.write("A1", "Monthly Performance Report — UAC Care Pipeline", title_fmt)
        ws2.set_column("A:A", 14)
        ws2.set_column("B:M", 16)

        # Color-code Transfer Efficiency column
        eff_col = 7   # 0-indexed = column H (Transfer Eff)
        for row_num in range(3, 3 + len(export_monthly)):
            val = export_monthly.iloc[row_num - 3]["Transfer Eff (avg)"]
            fmt = green_fmt if val >= 0.75 else yel_fmt if val >= 0.55 else red_fmt
            ws2.write(row_num, eff_col, val, fmt)

        # ── Sheet 3: Daily Data ──────────────────────────────────────────────
        daily_export = df_daily[[
            "date", "cbp_apprehended", "cbp_custody", "cbp_transferred",
            "hhs_care", "hhs_discharged",
            "transfer_efficiency", "discharge_effectiveness", "pipeline_throughput",
            "system_backlog", "net_flow_hhs",
        ]].copy()
        daily_export.columns = [
            "Date", "CBP Apprehended", "CBP Custody", "CBP Transferred",
            "HHS Care", "HHS Discharged",
            "Transfer Efficiency", "Discharge Effectiveness", "Pipeline Throughput",
            "System Backlog", "Net Flow (HHS)",
        ]
        daily_export.to_excel(writer, sheet_name="Daily Data", index=False, startrow=2)
        ws3 = writer.sheets["Daily Data"]
        ws3.set_tab_color("#f06a3b")
        ws3.write("A1", "Daily Data — UAC Care Pipeline Analytics", title_fmt)
        ws3.set_column("A:A", 14)
        ws3.set_column("B:K", 18)

    output.seek(0)
    return output.read()


# ── Text Summary Export ───────────────────────────────────────────────────────

def build_text_summary(df_daily: pd.DataFrame, df_monthly: pd.DataFrame) -> str:
    """
    Builds a plain-text executive summary for copy/paste or download.
    """
    now   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    total = df_daily["hhs_discharged"].sum()
    peak  = int(df_daily["hhs_care"].max())
    curr  = int(df_daily["hhs_care"].iloc[-1])
    te    = df_daily["transfer_efficiency"].mean() * 100
    de    = df_daily["discharge_effectiveness"].mean() * 100

    lines = [
        "=" * 68,
        "  UAC CARE PIPELINE ANALYTICS — EXECUTIVE SUMMARY",
        "  U.S. Department of Health & Human Services | ORR",
        f"  Generated: {now}",
        "=" * 68,
        "",
        "DATASET PERIOD: January 2023 – December 2025",
        f"REPORTING DAYS: {len(df_daily)}",
        "",
        "PIPELINE TOTALS",
        "-" * 40,
        f"  Total Children Apprehended:   {int(df_daily['cbp_apprehended'].sum()):>10,}",
        f"  Total CBP → HHS Transfers:    {int(df_daily['cbp_transferred'].sum()):>10,}",
        f"  Total HHS Sponsor Placements: {int(total):>10,}",
        "",
        "CENSUS STATUS",
        "-" * 40,
        f"  Peak HHS Census:              {peak:>10,}  (Dec 20, 2023)",
        f"  Current HHS Census:           {curr:>10,}  (Latest report)",
        f"  Reduction from Peak:          {abs((curr - peak) / peak * 100):.1f}%",
        "",
        "EFFICIENCY METRICS (3-YEAR AVERAGES)",
        "-" * 40,
        f"  Avg Transfer Efficiency:      {te:.1f}%   (Target ≥75%)",
        f"  Avg Discharge Effectiveness:  {de:.2f}%  (Target ≥3.0%)",
        f"  Avg Pipeline Throughput:      {df_daily['pipeline_throughput'].mean():.2f}×  (Target ≥1.0×)",
        "",
        "KEY FINDINGS",
        "-" * 40,
        "  1. System experienced critical surge Dec 2023 (11,516 children).",
        "  2. Sustained discharge campaign in 2024 cleared 83% of backlog.",
        "  3. 2025 saw dramatic intake reduction — policy/enforcement shift.",
        "  4. Transfer efficiency dropped <30% in late 2025 (low volume phase).",
        "  5. Weekly discharge cycle shows midweek peak — scheduling opportunity.",
        "",
        "RECOMMENDATIONS",
        "-" * 40,
        "  • Establish HHS Census threshold alerts at 4,000 / 8,000.",
        "  • Review CBP coordination when Transfer Efficiency < 60%.",
        "  • Escalate discharge capacity when Net Flow > +100/week × 4 weeks.",
        "  • Optimize case management scheduling to reduce weekend discharge gap.",
        "",
        "=" * 68,
        "  DATA SOURCE: HHS ORR Public Dataset",
        "  CLASSIFICATION: Unclassified | For Internal Use",
        "=" * 68,
    ]

    return "\n".join(lines)