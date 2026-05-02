"""
main.py
=======
Streamlit entry point for the UAC Care Pipeline Analytics Dashboard.
Run with:  streamlit run app/main.py
"""

import streamlit as st
import os, sys, importlib, importlib.util

# ── Path Setup ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES_DIR = os.path.join(ROOT, "pages")

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.config import APP_TITLE, APP_SUBTITLE, APP_ICON, APP_VERSION, COLORS
from utils.data_loader import system_kpis

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title            = APP_TITLE,
    page_icon             = APP_ICON,
    layout                = "wide",
    initial_sidebar_state = "expanded",
    menu_items={"Get help": None, "Report a bug": None,
                "About": f"**{APP_TITLE}** v{APP_VERSION}\n\n{APP_SUBTITLE}"},
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
css_path = os.path.join(ROOT, "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Auto-detect page files ────────────────────────────────────────────────────
# Scans the pages/ folder and matches files by number prefix (01, 02 ...)
# Works regardless of whether files are named p01_overview.py or 01_overview.py

def _find_page_file(number: str) -> str:
    """Return the full path of the page file that starts with `number`."""
    for fname in os.listdir(PAGES_DIR):
        if fname.endswith(".py") and not fname.startswith("_"):
            # match "01", "p01", "01_", "p01_" etc.
            stripped = fname.replace("p", "", 1) if fname.startswith("p") else fname
            if stripped.startswith(number):
                return os.path.join(PAGES_DIR, fname)
    return ""

# Map: sidebar label → file number prefix
PAGE_MAP = {
    "📊  System Overview":      "01",
    "⚡  Efficiency Analytics": "02",
    "📈  Backlog Detection":    "03",
    "🎯  Outcome Trends":       "04",
    "📋  Monthly Report":       "05",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"""
        <div style="padding:16px 0 8px;
                    border-bottom:1px solid {COLORS['border']};
                    margin-bottom:16px">
          <div style="font-family:Syne,sans-serif; font-size:16px; font-weight:800;
                      color:{COLORS['text']}; line-height:1.2; letter-spacing:-0.01em">
            UAC Care Pipeline
          </div>
          <div style="font-size:10px; color:{COLORS['muted']}; letter-spacing:0.08em;
                      text-transform:uppercase; margin-top:4px">
            HHS / ORR Analytics
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected = st.radio(
        "Navigation",
        options=list(PAGE_MAP.keys()),
        label_visibility="collapsed",
    )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.divider()

    # ── Quick Stats ───────────────────────────────────────────────────────────
    try:
        kpis = system_kpis()
        st.markdown(
            f"<div style='font-size:9px;letter-spacing:0.1em;text-transform:uppercase;"
            f"color:{COLORS['muted']};margin-bottom:10px'>Live Snapshot</div>",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            st.metric("HHS Census", f"{kpis['current_hhs_care']:,}",
                      delta=f"{kpis['pct_change_from_peak']:.1f}% from peak",
                      delta_color="inverse")
        with c2:
            st.metric("Transfer Eff", f"{kpis['recent_transfer_eff']:.1f}%",
                      delta="30-day avg", delta_color="off")
        st.markdown(
            f"<div style='font-size:9px;color:{COLORS['muted']};margin-top:10px;"
            f"font-family:DM Mono,monospace;line-height:1.7'>"
            f"Dataset: Jan 2023 – Dec 2025<br>"
            f"Records: {kpis['total_days']} reporting days<br>"
            f"Version: v{APP_VERSION}</div>",
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.warning(f"Snapshot unavailable: {e}")

    st.divider()
    st.markdown(
        f"<div style='font-size:9px;color:{COLORS['muted']};"
        f"font-family:DM Mono,monospace;line-height:1.7'>"
        f"U.S. Dept. of Health &amp; Human Services<br>"
        f"Office of Refugee Resettlement<br>"
        f"Data Source: HHS ORR Public Dataset</div>",
        unsafe_allow_html=True,
    )

# ── Page Routing ──────────────────────────────────────────────────────────────
page_number  = PAGE_MAP[selected]           # e.g. "01"
page_path    = _find_page_file(page_number) # full .py path, auto-detected

# Debug: show what we found (remove after confirming it works)
if not page_path:
    st.error(
        f"❌ Cannot find page file for prefix **'{page_number}'** "
        f"inside `{PAGES_DIR}`\n\n"
        f"Files found: `{os.listdir(PAGES_DIR)}`"
    )
    st.stop()

try:
    spec = importlib.util.spec_from_file_location("page_module", page_path)
    page = importlib.util.module_from_spec(spec)
    # Inject ROOT into the page module so its own imports resolve
    page.__package__ = ""
    sys.modules["page_module"] = page
    spec.loader.exec_module(page)
    page.render()
except Exception as e:
    st.error(f"Failed to load: `{page_path}`")
    st.exception(e)