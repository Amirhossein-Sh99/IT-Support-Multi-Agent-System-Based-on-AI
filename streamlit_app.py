"""
Streamlit web UI for the IT-Support Multi-Agent System.

Run locally:
    streamlit run streamlit_app.py

Deploy for free on Streamlit Community Cloud (share.streamlit.io):
    1. Push this repo to a public GitHub repository.
    2. Go to share.streamlit.io -> "New app" -> pick this repo and branch.
    3. Set "Main file path" to streamlit_app.py
    4. In the app's Settings -> Secrets, add:
           GOOGLE_API_KEY = "your_key_here"
    5. Deploy - you'll get a public URL to put in your Kaggle Writeup.
"""

import asyncio
import os
import re

import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except Exception:
    pass  # No secrets.toml - normal when running locally with a .env file instead.

from src.pipeline import process_ticket_streaming, extract_field  # noqa: E402
from src.memory import save_ticket, list_all_tickets  # noqa: E402

STEP_ORDER = ["triage_agent", "diagnostics_agent", "documentation_agent"]
STEP_LABELS = {"triage_agent": "Triage", "diagnostics_agent": "Diagnostics", "documentation_agent": "Documentation"}
URGENCY_LEVELS = ["critical", "high", "medium", "low"]


def step_html(key: str, state: str) -> str:
    icon = "✓" if state == "done" else ""
    return (
        f'<div class="step step-{state}">'
        f'<span class="step-num">STEP {STEP_ORDER.index(key) + 1}</span>'
        f'<span class="step-label">{icon + " " if icon else ""}{STEP_LABELS[key]}</span>'
        f"</div>"
    )


def parse_sections(text: str) -> dict:
    """Splits the documentation agent's markdown output into named sections."""
    parts = re.split(r"\n(?=##\s)", text.strip())
    sections = {}
    for part in parts:
        lines = part.strip().split("\n", 1)
        header = lines[0].lstrip("#").strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        sections[header] = body
    return sections


def urgency_pill(urgency: str) -> str:
    level = urgency.lower() if urgency.lower() in URGENCY_LEVELS else "unknown"
    return f'<span class="urgency-pill urgency-{level}">{urgency}</span>'


st.set_page_config(
    page_title="IT-Support Multi-Agent System",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Design system. Palette: near-black ink on a clean white/cool-grey surface
# for maximum readability (this is a working tool, not a marketing page).
# Teal is the single accent color; amber/red are reserved strictly for
# urgency signaling, matching how real ticketing tools (Zendesk, Freshdesk,
# ServiceNow) use color as information, not decoration.
#
# IMPORTANT: rules target both custom classes AND Streamlit's own native
# elements (headers, tabs, expanders, captions, inputs) - a common mistake
# is only styling custom <div>s and leaving native widgets at Streamlit's
# default muted grey, which is what caused the low-contrast look before.
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg: #EEF1F4;
    --surface: #FFFFFF;
    --ink: #101820;
    --ink-soft: #33404A;
    --muted: #647080;
    --border: #DCE1E7;
    --accent: #0F7A73;
    --accent-dark: #0B5C57;
    --accent-soft: #E1F1EE;
    --amber: #A8630A;
    --amber-soft: #FBEEDC;
    --red: #B23A2E;
    --red-soft: #FBE7E4;
    --shadow: 0 1px 2px rgba(16,24,32,0.04), 0 4px 14px rgba(16,24,32,0.06);
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    color: var(--ink) !important;
}

.stApp { background: var(--bg); }
.block-container { padding-top: 2rem; max-width: 780px; }

/* Force strong, consistent color on every native Streamlit text element -
   this is what actually fixes the washed-out / low-contrast look. */
h1, h2, h3, h4, h5, h6 { color: var(--ink) !important; font-weight: 700 !important; }
p, span, label { color: var(--ink-soft); }
.stMarkdown, .stMarkdown p { color: var(--ink-soft) !important; }
.stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] {
    color: var(--muted) !important;
    font-weight: 600;
    font-size: 0.95rem;
    padding: 10px 4px;
}
.stTabs [aria-selected="true"] {
    color: var(--accent-dark) !important;
    border-bottom: 2.5px solid var(--accent) !important;
}

/* Expander */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    background: var(--surface);
}
[data-testid="stExpander"] summary { font-weight: 600 !important; color: var(--ink) !important; }

/* Text input / textarea / selectbox: strong border so they never look
   "empty" or non-interactive */
.stTextArea textarea, .stTextInput input {
    border: 1.5px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--ink) !important;
    background: var(--surface) !important;
    font-size: 0.95rem !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-soft) !important;
}
div[data-baseweb="select"] > div {
    border: 1.5px solid var(--border) !important;
    border-radius: 10px !important;
    background: var(--surface) !important;
}
div[data-baseweb="select"] * { color: var(--ink) !important; }

/* Header bar */
.app-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 4px;
}
.app-header .icon {
    font-size: 1.6rem;
}
.hero-title {
    font-size: 1.7rem;
    font-weight: 800;
    color: var(--ink);
    letter-spacing: -0.02em;
    margin: 0;
}
.hero-sub {
    color: var(--muted) !important;
    font-size: 0.98rem;
    margin: 6px 0 20px 0;
    line-height: 1.55;
}

.field-label {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--ink-soft) !important;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 22px 24px;
    margin-bottom: 18px;
    box-shadow: var(--shadow);
}

/* Stepper */
.step {
    border: 1.5px solid var(--border);
    border-radius: 12px;
    padding: 14px 12px;
    text-align: center;
    background: var(--surface);
    transition: all 0.2s ease;
}
.step-pending { color: var(--muted) !important; }
.step-pending .step-label { color: var(--muted) !important; }
.step-active {
    border-color: var(--accent);
    background: var(--accent-soft);
}
.step-active .step-label, .step-active .step-num { color: var(--accent-dark) !important; }
.step-done {
    border-color: var(--accent-dark);
    background: var(--accent);
}
.step-done .step-label, .step-done .step-num { color: #FFFFFF !important; }
.step-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    opacity: 0.85;
    display: block;
    margin-bottom: 2px;
    letter-spacing: 0.04em;
}
.step-label { font-weight: 700; font-size: 0.87rem; }

/* Technical trace - a real terminal-style log, with an obvious scrollbar
   and a visible affordance instead of a mystery box you have to hover to
   discover is scrollable. */
.trace-wrap { position: relative; }
.trace-block {
    background: #FAFBFC;
    color: #16202A;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    border-radius: 12px;
    padding: 16px 18px;
    white-space: pre-wrap;
    line-height: 1.6;
    max-height: 230px;
    overflow-y: scroll;
    border: 1.5px solid var(--border);
}
.trace-block::-webkit-scrollbar { width: 10px; }
.trace-block::-webkit-scrollbar-track { background: #FAFBFC; border-radius: 12px; }
.trace-block::-webkit-scrollbar-thumb {
    background: var(--accent);
    border-radius: 12px;
    border: 2px solid #FAFBFC;
}
.trace-hint {
    font-size: 0.72rem;
    color: var(--muted) !important;
    margin: 6px 2px 14px 2px;
}

.report-section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px 26px;
    margin-bottom: 14px;
    line-height: 1.7;
    box-shadow: var(--shadow);
}
.report-section h3 {
    font-size: 0.82rem !important;
    color: var(--accent-dark) !important;
    margin-top: 0 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 800 !important;
}
.report-section p, .report-section li, .report-section strong {
    color: var(--ink-soft) !important;
}

.urgency-pill {
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    padding: 3px 10px;
    border-radius: 20px;
}
.urgency-critical { background: var(--red-soft); color: var(--red) !important; }
.urgency-high { background: var(--amber-soft); color: var(--amber) !important; }
.urgency-medium { background: var(--accent-soft); color: var(--accent-dark) !important; }
.urgency-low { background: #EAEDF0; color: var(--muted) !important; }
.urgency-unknown { background: #EAEDF0; color: var(--muted) !important; }

.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 18px 16px;
    text-align: center;
    box-shadow: var(--shadow);
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--ink) !important;
    font-family: 'JetBrains Mono', monospace;
}
.metric-label {
    color: var(--muted) !important;
    font-size: 0.76rem;
    margin-top: 2px;
    font-weight: 600;
}

.ticket-row {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 13px 16px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
}
.ticket-row-text { font-size: 0.9rem; color: var(--ink) !important; flex: 1; font-weight: 500; }
.ticket-row-meta {
    font-size: 0.74rem;
    color: var(--muted) !important;
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
}

div.stButton > button, div.stFormSubmitButton > button {
    background: var(--ink) !important;
    color: #FFFFFF !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 0.6rem 1.5rem !important;
    font-weight: 700 !important;
}
div.stButton > button *, div.stFormSubmitButton > button * {
    color: #FFFFFF !important;
}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {
    background: var(--accent-dark) !important;
    color: #FFFFFF !important;
}
div.stButton > button:hover *, div.stFormSubmitButton > button:hover * {
    color: #FFFFFF !important;
}
[data-testid="stForm"] {
    border: 1.5px solid var(--border) !important;
    border-radius: 16px !important;
    background: var(--surface) !important;
    padding: 22px 24px !important;
    box-shadow: var(--shadow) !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Top-level navigation
# ---------------------------------------------------------------------------
tab_submit, tab_dashboard = st.tabs(["🎫 Submit a Ticket", "📊 Ops Dashboard"])

with tab_submit:
    st.markdown(
        '<div class="app-header"><span class="icon">🛠️</span>'
        '<span class="hero-title">IT-Support Multi-Agent System</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hero-sub">Three agents turn a raw IT ticket into a diagnosed, '
        'documented, bilingual (EN/DE) resolution report — Triage → Diagnostics → Documentation.</div>',
        unsafe_allow_html=True,
    )

    with st.expander("ℹ️ How this works"):
        st.markdown(
            """
- **Triage Agent** classifies the ticket (network / hardware / software / access) and sets urgency.
- **Diagnostics Agent** investigates via an MCP server (network check, traceroute, log search, service status) and checks memory for similar past tickets.
- **Documentation Agent** writes the final report: executive summary, root cause, diagnostic timeline, actions taken, next steps, preventive measures, a German summary, and a knowledge-base entry.
            """
        )

    examples = [
        "— write your own below, or pick an example —",
        "I can't connect to the office VPN since this morning.",
        "My laptop screen keeps flickering and sometimes goes black.",
        "I forgot my password and can't log in to my account.",
        "Excel keeps crashing every time I open a large spreadsheet.",
    ]

    # The form itself is styled as the card (see [data-testid="stForm"] CSS
    # above) - no manual <div> wrapper needed here, which previously caused
    # a stray empty box due to the opening/closing tags living in separate
    # st.markdown calls.
    with st.form(key="ticket_form", clear_on_submit=False):
        st.markdown('<div class="field-label">Quick-start with an example</div>', unsafe_allow_html=True)
        choice = st.selectbox("Example tickets", examples, label_visibility="collapsed")

        st.markdown('<div class="field-label" style="margin-top:14px;">Describe the IT issue</div>', unsafe_allow_html=True)
        default_text = "" if choice == examples[0] else choice
        ticket_text = st.text_area(
            "Ticket description",
            value=default_text,
            height=90,
            placeholder="e.g. My printer shows an error and won't print anything…",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Submit ticket →", type="primary")

    if submitted and not ticket_text.strip():
        st.warning("Write a short description of the issue first.")

    if submitted and ticket_text.strip():
        cols = st.columns(3)
        placeholders = {}
        for i, key in enumerate(STEP_ORDER):
            with cols[i]:
                state = "active" if i == 0 else "pending"
                placeholders[key] = st.empty()
                placeholders[key].markdown(step_html(key, state), unsafe_allow_html=True)

        trace_hint = st.empty()
        trace_box = st.empty()
        results = {}
        error_placeholder = st.empty()

        async def run_pipeline():
            trace_lines = []
            try:
                async for update in process_ticket_streaming(ticket_text):
                    agent = update["agent"]
                    results[agent] = update["text"]
                    placeholders[agent].markdown(step_html(agent, "done"), unsafe_allow_html=True)
                    idx = STEP_ORDER.index(agent)
                    if idx + 1 < len(STEP_ORDER):
                        next_key = STEP_ORDER[idx + 1]
                        placeholders[next_key].markdown(step_html(next_key, "active"), unsafe_allow_html=True)

                    if agent == "documentation_agent":
                        trace_lines.append(f"[{agent}]\nFull report generated - see 'Resolution Report' below.")
                    else:
                        trace_lines.append(f"[{agent}]\n{update['text']}")
            except RuntimeError as e:
                error_placeholder.error(str(e))
                return

            # Render the full trace once, after every agent has finished,
            # instead of re-rendering it on every intermediate step - this
            # avoids catching Streamlit mid-update in a half-rendered state.
            joined_trace = "\n\n".join(trace_lines)
            trace_hint.markdown(
                '<div class="trace-hint">↕ Full agent trace — scroll inside the box for more</div>',
                unsafe_allow_html=True,
            )
            trace_box.markdown(
                f'<div class="trace-block">{joined_trace}</div>',
                unsafe_allow_html=True,
            )

        asyncio.run(run_pipeline())

        if "triage_agent" in results and "diagnostics_agent" in results:
            save_ticket(
                ticket_text=ticket_text,
                category=extract_field(results["triage_agent"], "Category"),
                urgency=extract_field(results["triage_agent"], "Urgency"),
                root_cause=extract_field(results["diagnostics_agent"], "Root Cause"),
                fix=extract_field(results["diagnostics_agent"], "Proposed Fix"),
            )

        if "documentation_agent" in results:
            sections = parse_sections(results["documentation_agent"])
            st.markdown("#### Resolution Report")

            tab_en, tab_de, tab_kb = st.tabs(["🇬🇧 English", "🇩🇪 Deutsch", "📚 Knowledge Base"])

            with tab_en:
                for header in [
                    "Executive Summary",
                    "Root Cause",
                    "Diagnostic Timeline",
                    "Actions Taken",
                    "Recommended Next Steps",
                    "Preventive Measures",
                ]:
                    if header in sections:
                        st.markdown(
                            f'<div class="report-section"><h3>{header}</h3>{sections[header]}</div>',
                            unsafe_allow_html=True,
                        )
            with tab_de:
                de_key = next((k for k in sections if "Zusammenfassung" in k), None)
                if de_key:
                    st.markdown(
                        f'<div class="report-section"><h3>{de_key}</h3>{sections[de_key]}</div>',
                        unsafe_allow_html=True,
                    )
            with tab_kb:
                kb_key = next((k for k in sections if "Knowledge Base" in k), None)
                if kb_key:
                    st.markdown(
                        f'<div class="report-section"><h3>{kb_key}</h3>{sections[kb_key]}</div>',
                        unsafe_allow_html=True,
                    )

with tab_dashboard:
    st.markdown('<div class="hero-title">Ops Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">Every ticket this system has resolved, pulled from long-term memory.</div>',
        unsafe_allow_html=True,
    )

    tickets = list_all_tickets()

    if not tickets:
        st.info("No tickets resolved yet. Submit one in the first tab, then come back here.")
    else:
        category_counts = {}
        for t in tickets:
            category_counts[t.get("category", "unknown")] = category_counts.get(t.get("category", "unknown"), 0) + 1

        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(
                f'<div class="metric-card"><div class="metric-value">{len(tickets)}</div>'
                '<div class="metric-label">Tickets resolved</div></div>',
                unsafe_allow_html=True,
            )
        with m2:
            most_common = max(category_counts, key=category_counts.get)
            st.markdown(
                f'<div class="metric-card"><div class="metric-value">{most_common}</div>'
                '<div class="metric-label">Most common category</div></div>',
                unsafe_allow_html=True,
            )
        with m3:
            critical_count = sum(1 for t in tickets if t.get("urgency", "").lower() in ("high", "critical"))
            st.markdown(
                f'<div class="metric-card"><div class="metric-value">{critical_count}</div>'
                '<div class="metric-label">High/critical tickets</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        urgency_counts = {}
        for t in tickets:
            u = t.get("urgency", "unknown").lower()
            urgency_counts[u] = urgency_counts.get(u, 0) + 1

        urgency_colors = {
            "critical": "#B23A2E",
            "high": "#A8630A",
            "medium": "#0F7A73",
            "low": "#8B96A3",
            "unknown": "#8B96A3",
        }

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            cat_fig = px.bar(
                x=list(category_counts.keys()),
                y=list(category_counts.values()),
                labels={"x": "", "y": "Tickets"},
                title="Tickets by Category",
            )
            cat_fig.update_traces(marker_color="#0F7A73")
            cat_fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(family="Inter, sans-serif", color="#101820"),
                title_font=dict(size=14, color="#101820"),
                margin=dict(l=10, r=10, t=40, b=10),
                height=260,
            )
            st.plotly_chart(cat_fig, use_container_width=True)

        with chart_col2:
            urgency_fig = px.bar(
                x=list(urgency_counts.keys()),
                y=list(urgency_counts.values()),
                labels={"x": "", "y": "Tickets"},
                title="Tickets by Urgency",
            )
            bar_colors = [urgency_colors.get(u, "#8B96A3") for u in urgency_counts.keys()]
            urgency_fig.update_traces(marker_color=bar_colors)
            urgency_fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(family="Inter, sans-serif", color="#101820"),
                title_font=dict(size=14, color="#101820"),
                margin=dict(l=10, r=10, t=40, b=10),
                height=260,
            )
            st.plotly_chart(urgency_fig, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Ticket Queue")

        for t in tickets:
            ts = t.get("timestamp", "")[:16].replace("T", " ")
            st.markdown(
                f'<div class="ticket-row">'
                f'<div class="ticket-row-text">{t["ticket_text"][:90]}</div>'
                f'<div class="ticket-row-meta">{urgency_pill(t.get("urgency", "unknown"))} '
                f'&nbsp;{t.get("category", "unknown")} &nbsp;·&nbsp; {ts}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
            with st.expander("Root cause & fix"):
                st.write(f"**Root cause:** {t.get('root_cause', 'n/a')}")
                st.write(f"**Fix:** {t.get('fix', 'n/a')}")
