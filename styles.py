"""
Visual theme for the Supplier Bill Management System.

Design concept: a trusted paper ledger, not a generic SaaS dashboard.
- Public Sans for interface text (plain, sturdy, legible)
- IBM Plex Mono for figures only (amounts, invoice numbers, item codes)
  so numbers line up the way they would on a real ledger
- Status colour is functional, not decorative:
    ledger-green = verified / paid
    stamp-amber  = pending / unpaid
    stamp-rust   = overdue / attention
"""

import streamlit as st


def load_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        :root {
            --ink: #1B2321;
            --paper: #F1F0EB;
            --surface: #FFFFFF;
            --ledger-green: #2F5D50;
            --ledger-green-dark: #23473C;
            --stamp-amber: #A6742C;
            --stamp-rust: #9C3B2E;
            --line: #D9D6CC;
            --text-muted: #5B6462;
        }

        html, body, [class*="css"], .stApp, .stMarkdown, p, span, div, label {
            font-family: 'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .stApp {
            background-color: var(--paper);
            color: var(--ink);
        }

        /* ---------------------------------------------------- */
        /* Hide default Streamlit chrome for a fully custom look */
        /* ---------------------------------------------------- */
        #MainMenu, header, footer,
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"] {
            visibility: hidden;
            height: 0;
            position: fixed;
        }

        /* ---------------------------------------------------- */
        /* Headings                                              */
        /* ---------------------------------------------------- */
        h1, h2, h3, h4 {
            font-family: 'Public Sans', sans-serif;
            font-weight: 600;
            letter-spacing: -0.01em;
            color: var(--ink);
        }

        h1 {
            border-bottom: 1px solid var(--line);
            padding-bottom: 0.65rem;
            margin-bottom: 1.25rem;
        }

        hr { border-color: var(--line); }

        /* ---------------------------------------------------- */
        /* Sidebar -> nav rail                                   */
        /* ---------------------------------------------------- */
        [data-testid="stSidebar"] {
            background-color: var(--surface);
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] [role="radiogroup"] label {
            border-left: 3px solid transparent;
            padding: 0.45rem 0.75rem;
            margin-bottom: 2px;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            background-color: var(--paper);
            border-left-color: var(--line);
        }

        /* ---------------------------------------------------- */
        /* Buttons                                               */
        /* ---------------------------------------------------- */
        .stButton > button, .stDownloadButton > button {
            border-radius: 4px;
            border: 1px solid var(--line);
            background-color: var(--surface);
            color: var(--ink);
            font-weight: 500;
            box-shadow: none;
            transition: background-color 0.15s ease, border-color 0.15s ease;
        }

        .stButton > button:hover, .stDownloadButton > button:hover {
            border-color: var(--ledger-green);
            color: var(--ledger-green-dark);
        }

        .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
            background-color: var(--ledger-green);
            border-color: var(--ledger-green);
            color: #FFFFFF;
        }

        .stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
            background-color: var(--ledger-green-dark);
            border-color: var(--ledger-green-dark);
            color: #FFFFFF;
        }

        /* ---------------------------------------------------- */
        /* Inputs                                                */
        /* ---------------------------------------------------- */
        .stTextInput input, .stNumberInput input, .stTextArea textarea,
        .stDateInput input, .stSelectbox div[data-baseweb="select"] > div {
            border-radius: 4px;
            border-color: var(--line) !important;
        }

        /* ---------------------------------------------------- */
        /* Metrics                                               */
        /* ---------------------------------------------------- */
        [data-testid="stMetric"] {
            background-color: var(--surface);
            border: 1px solid var(--line);
            border-radius: 4px;
            padding: 1rem 1.1rem;
        }

        [data-testid="stMetricValue"] {
            font-family: 'IBM Plex Mono', monospace;
            color: var(--ink);
        }

        [data-testid="stMetricLabel"] {
            color: var(--text-muted);
        }

        /* ---------------------------------------------------- */
        /* Tables / dataframes - figures in mono                */
        /* ---------------------------------------------------- */
        [data-testid="stDataFrame"] {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.9rem;
            border: 1px solid var(--line);
            border-radius: 4px;
        }

        /* ---------------------------------------------------- */
        /* Alerts                                                */
        /* ---------------------------------------------------- */
        div[data-testid="stAlert"] {
            border-radius: 4px;
            border: 1px solid var(--line);
        }

        /* ---------------------------------------------------- */
        /* Tabs                                                  */
        /* ---------------------------------------------------- */
        .stTabs [data-baseweb="tab-list"] {
            border-bottom: 1px solid var(--line);
            gap: 1.5rem;
        }

        .stTabs [aria-selected="true"] {
            color: var(--ledger-green-dark) !important;
            border-bottom-color: var(--ledger-green) !important;
        }

        /* ---------------------------------------------------- */
        /* Status badges (replaces checkmark / warning emoji)    */
        /* ---------------------------------------------------- */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            font-family: 'Public Sans', sans-serif;
            font-size: 0.92rem;
            font-weight: 500;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
        }

        .status-verified { color: var(--ledger-green-dark); }
        .status-verified .status-dot { background-color: var(--ledger-green); }

        .status-pending { color: var(--stamp-amber); }
        .status-pending .status-dot { background-color: var(--stamp-amber); }

        .status-overdue { color: var(--stamp-rust); }
        .status-overdue .status-dot { background-color: var(--stamp-rust); }

        /* ---------------------------------------------------- */
        /* Login card                                            */
        /* ---------------------------------------------------- */
        .login-card {
            background-color: var(--surface);
            border: 1px solid var(--line);
            border-radius: 6px;
            padding: 2.5rem 2.5rem 1.75rem 2.5rem;
            margin-top: 2rem;
        }

        .login-card h1 {
            border-bottom: none;
            padding-bottom: 0;
            margin-bottom: 0.25rem;
            font-size: 1.4rem;
        }

        .login-subtitle {
            color: var(--text-muted);
            margin-bottom: 1.5rem;
            font-size: 0.95rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_status(label, kind="verified"):
    """
    Renders a small coloured status indicator in place of an emoji.
    kind: "verified" (ledger green), "pending" (amber), "overdue" (rust)
    """
    st.markdown(
        f'<div class="status-badge status-{kind}">'
        f'<span class="status-dot"></span>{label}</div>',
        unsafe_allow_html=True,
    )
