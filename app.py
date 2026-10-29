import calendar
import hmac
import html as html_lib
import inspect
import io
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import altair as alt
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="SYComms Renewals & Sales Command Center", page_icon="📅", layout="wide"
)

UK_TZ = ZoneInfo("Europe/London")


# --- Prospect Engine styling (design system shared across Sam's apps) ---
# Presentation only — no business logic. The dataframe grid's own colours
# can't be reached by CSS, which is why the matching dark theme also lives in
# .streamlit/config.toml alongside this file.
_PE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--bg:#0A0E1A;--surface:#111827;--surface-2:#161F33;--surface-3:#1C2740;--border:rgba(148,163,184,.14);--border-strong:rgba(148,163,184,.26);--text:#E7EAF3;--muted:#8C98B0;--faint:#5E6A82;--accent:#7C83FF;--accent-2:#38D6F5;--accent-soft:rgba(124,131,255,.14);--good:#34D399;--warn:#FBBF24;--risk:#FB923C;--bad:#F87171;--radius:14px;--grad:linear-gradient(135deg,#7C83FF 0%,#38D6F5 100%);}
html,body,[class*="css"],.stApp,button,input,textarea,select{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif!important}
.stApp{background:radial-gradient(1200px 500px at 85% -10%,rgba(56,214,245,.07),transparent 60%),radial-gradient(900px 500px at 10% -20%,rgba(124,131,255,.10),transparent 60%),var(--bg)}
[data-testid="stHeader"]{background:transparent}[data-testid="stDecoration"]{display:none}footer{visibility:hidden}
.block-container{padding-top:1.6rem!important;padding-bottom:3rem!important;max-width:1500px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0D1322 0%,#0A0E1A 100%);border-right:1px solid var(--border)}
[data-testid="stWidgetLabel"] p{font-size:.76rem!important;font-weight:600!important;color:var(--muted)!important;text-transform:uppercase;letter-spacing:.06em}
[data-testid="stCaptionContainer"]{color:var(--muted)!important}
[class*="st-key-card-"]{background:linear-gradient(180deg,rgba(22,31,51,.85) 0%,rgba(17,24,39,.85) 100%);border:1px solid var(--border)!important;border-radius:var(--radius);padding:22px 22px 18px;box-shadow:0 1px 0 rgba(255,255,255,.03) inset,0 20px 40px -24px rgba(0,0,0,.6);margin-bottom:18px}
[class*="st-key-appt-"],[class*="st-key-day-"]{background:linear-gradient(180deg,rgba(22,31,51,.7) 0%,rgba(17,24,39,.7) 100%);border:1px solid var(--border)!important;border-radius:12px;padding:14px 16px 10px;box-shadow:0 1px 0 rgba(255,255,255,.03) inset;margin-bottom:10px}
[data-baseweb="input"],[data-baseweb="select"]>div,[data-baseweb="textarea"]{background:var(--surface)!important;border:1px solid var(--border-strong)!important;border-radius:10px!important}
[data-baseweb="input"]:focus-within,[data-baseweb="select"]>div:focus-within,[data-baseweb="textarea"]:focus-within{border-color:var(--accent)!important;box-shadow:0 0 0 3px var(--accent-soft)!important}
[data-baseweb="input"]>div,[data-baseweb="base-input"]{background:transparent!important}
.stButton button,.stDownloadButton button,.stFormSubmitButton button{border-radius:10px!important;font-weight:600!important;border:1px solid var(--border-strong)!important;background:var(--surface-2)!important;color:var(--text)!important;transition:all .15s ease}
.stButton button:hover,.stDownloadButton button:hover{border-color:var(--accent)!important;transform:translateY(-1px)}
.stButton button[kind="primary"],.stDownloadButton button[kind="primary"],.stFormSubmitButton button,[data-testid="stBaseButton-primary"],[data-testid="stBaseLinkButton-primary"]{background:var(--grad)!important;border:none!important;color:#0A0E1A!important;box-shadow:0 8px 24px -10px rgba(124,131,255,.8)}
.stButton button[kind="primary"] p,[data-testid="stBaseButton-primary"] p,.stFormSubmitButton button p,[data-testid="stBaseLinkButton-primary"] p{color:#0A0E1A!important;font-weight:700!important}
[data-testid="stTabs"] [role="tablist"],[data-baseweb="tab-list"]{gap:4px;background:var(--surface);padding:4px;border-radius:12px;border:1px solid var(--border);width:fit-content}
[data-testid="stTabs"] [role="tab"],[data-baseweb="tab"]{border-radius:9px!important;padding:8px 16px!important;color:var(--muted)!important;background:transparent!important}
[data-testid="stTabs"] [role="tab"][aria-selected="true"],[data-baseweb="tab"][aria-selected="true"]{background:var(--surface-3)!important;color:var(--text)!important}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"],[data-testid="stTabs"] .react-aria-SelectionIndicator{display:none!important}
[data-testid="stDataFrame"]{border:1px solid var(--border);border-radius:12px;overflow:hidden}
[data-testid="stExpander"] details{background:var(--surface);border:1px solid var(--border)!important;border-radius:12px!important}
[data-testid="stAlert"]{border-radius:12px!important}
.pe-hero{display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;padding:6px 2px 22px;margin-bottom:18px;border-bottom:1px solid var(--border)}
.pe-eyebrow{display:inline-flex;align-items:center;gap:8px;font-size:.72rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--accent-2);margin-bottom:8px}
.pe-eyebrow .dot{width:7px;height:7px;border-radius:50%;background:var(--good);box-shadow:0 0 0 4px rgba(52,211,153,.15)}
.pe-title{font-size:2.05rem;font-weight:800;letter-spacing:-.035em;line-height:1.1;color:var(--text)}
.pe-title span{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.pe-sub{color:var(--muted);font-size:.95rem;margin-top:8px;max-width:620px}
.pe-section{display:flex;align-items:center;gap:12px;margin-bottom:16px;scroll-margin-top:20px}
.pe-section .badge{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:var(--accent-soft);color:var(--accent);font-weight:800;font-size:.85rem;border:1px solid rgba(124,131,255,.3)}
.pe-section .t{font-size:1.08rem;font-weight:700;color:var(--text)}.pe-section .s{font-size:.82rem;color:var(--muted);margin-top:2px}
.pe-chip{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;font-size:.76rem;font-weight:600;background:var(--surface-3);color:var(--text);border:1px solid var(--border);white-space:nowrap}
.pe-chip.accent{background:var(--accent-soft);color:#B9BDFF;border-color:rgba(124,131,255,.3)}
.pe-chip.good{background:rgba(52,211,153,.12);color:var(--good);border-color:rgba(52,211,153,.3)}
.pe-chip.warn{background:rgba(251,191,36,.12);color:var(--warn);border-color:rgba(251,191,36,.3)}
.pe-chip.bad{background:rgba(248,113,113,.12);color:var(--bad);border-color:rgba(248,113,113,.3)}
.pe-logo{width:40px;height:40px;border-radius:12px;background:var(--grad);display:grid;place-items:center;color:#0A0E1A;font-weight:800;box-shadow:0 10px 24px -10px rgba(124,131,255,.9)}
.pe-brand{display:flex;align-items:center;gap:12px;margin-bottom:6px}
.pe-brand .name{font-weight:800;color:var(--text);font-size:1rem;letter-spacing:-.02em}
.pe-brand .tag{color:var(--muted);font-size:.76rem}
.pe-status-row{display:flex;align-items:center;gap:8px;font-size:.82rem;color:var(--muted);margin:14px 0 18px}
.pe-status-row .dot{width:7px;height:7px;border-radius:50%;background:var(--good);box-shadow:0 0 0 3px rgba(52,211,153,.15)}
.pe-mini-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:18px}
.pe-mini{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 12px}
.pe-mini .l{font-size:.66rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--faint)}
.pe-mini .v{font-size:1.25rem;font-weight:800;color:var(--text);margin-top:2px}
.pe-login-head{text-align:center;margin:6vh 0 22px}.pe-login-head .pe-logo{width:54px;height:54px;margin:0 auto 16px;border-radius:16px;font-size:1.1rem}
.pe-login-head .t{font-size:1.6rem;font-weight:800;letter-spacing:-.03em;color:var(--text)}.pe-login-head .s{color:var(--muted);font-size:.92rem;margin-top:6px}
.pe-kpi{background:var(--surface);border:1px solid var(--border);border-top:2px solid var(--accent);border-radius:14px;padding:16px 18px;height:100%}
.pe-kpi .l{font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.pe-kpi .v{font-size:1.8rem;font-weight:800;letter-spacing:-.03em;color:var(--text);margin-top:6px}
.pe-subhead{display:flex;align-items:center;gap:10px;margin:18px 0 8px;scroll-margin-top:20px}.pe-subhead .n{font-weight:600;color:var(--text)}.pe-kpi-link{display:block;text-decoration:none!important;cursor:pointer;transition:all .15s ease}
.pe-kpi-link:hover{border-color:var(--accent);transform:translateY(-2px);box-shadow:0 10px 24px -12px rgba(124,131,255,.6)}
.pe-kpi-link .l,.pe-kpi-link .v{display:block}.pe-kpi-link{min-height:112px;box-sizing:border-box;padding:16px 12px 16px 14px}.pe-kpi-link .l{font-size:.63rem;letter-spacing:.03em;overflow-wrap:normal;word-break:normal;hyphens:none;min-height:3.9em}
.pe-kpi-link .v{color:var(--accent-2)!important}
.pe-kpi{min-height:112px;box-sizing:border-box}
.pe-kpi.bad{border-top-color:var(--bad)}.pe-kpi.warn{border-top-color:var(--warn)}.pe-kpi.good{border-top-color:var(--good)}.pe-kpi.muted{border-top-color:var(--faint)}.pe-kpi.cyan{border-top-color:var(--accent-2)}
.pe-kpi-sub{font-size:.74rem;color:var(--muted);margin-top:2px}.pe-kpi-sub.good{color:var(--good)}.pe-kpi-sub.bad{color:var(--bad)}
.pe-callout{background:var(--surface-2);border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:12px;padding:12px 16px;margin:12px 0 4px;color:var(--text);font-size:.88rem;line-height:1.65}
.pe-callout b{color:#fff}
.pe-empty{display:flex;gap:16px;align-items:flex-start;padding:6px 2px}.pe-empty .ico{width:44px;height:44px;border-radius:12px;display:grid;place-items:center;background:var(--accent-soft);color:var(--accent);border:1px solid rgba(124,131,255,.3);flex:none}
.pe-empty .t{font-weight:700;color:var(--text);font-size:1rem;margin-bottom:6px}.pe-empty ol{margin:0;padding-left:1.1rem;color:var(--muted);font-size:.88rem;line-height:1.7}
.pe-anchor{scroll-margin-top:20px;height:0}
[data-testid="stMetric"]{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:14px 18px}
</style>
"""
st.markdown(_PE_CSS, unsafe_allow_html=True)


def esc(v):
    """Escapes any scraped or user-typed text before it goes into HTML —
    skipping this is how an account called 'Smith & Co' breaks the page."""
    return html_lib.escape(str(v if v is not None else ""), quote=True)


def render_html(markup, target=None):
    # Flatten lines: indented HTML inside st.markdown would otherwise render
    # as a code block rather than as HTML.
    (target or st).markdown("".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)


def chip(text, tone=""):
    return f'<span class="pe-chip {tone}">{esc(text)}</span>'


def section_header(num, title, subtitle="", anchor_id=None):
    id_attr = f' id="{esc(anchor_id)}"' if anchor_id else ""
    render_html(
        f'<div class="pe-section"{id_attr}><div class="badge">{num}</div><div><div class="t">{esc(title)}</div>'
        + (f'<div class="s">{esc(subtitle)}</div>' if subtitle else "")
        + "</div></div>"
    )


def kpi_tile(label, value, href=None, tone="", sub="", sub_tone=""):
    """One KPI tile. With href it becomes a clickable link that jumps to that
    section of the page (inline <span>s rather than <div>s inside the <a>, as
    block elements inside a link get split into separate links by the
    markdown renderer)."""
    if href:
        return (
            f'<a href="#{esc(href)}" class="pe-kpi pe-kpi-link {tone}">'
            f'<span class="l">{esc(label)} ↓</span><span class="v">{esc(value)}</span></a>'
        )
    sub_html = f'<div class="pe-kpi-sub {sub_tone}">{esc(sub)}</div>' if sub else ""
    return f'<div class="pe-kpi {tone}"><div class="l">{esc(label)}</div><div class="v">{esc(value)}</div>{sub_html}</div>'


def _full_width():
    try:
        if "width" in inspect.signature(st.button).parameters:
            return {"width": "stretch"}
    except (TypeError, ValueError):
        pass
    return {"use_container_width": True}


FULL_WIDTH = _full_width()
try:
    DF_WIDTH = {"width": "stretch"} if "width" in inspect.signature(st.dataframe).parameters else {"use_container_width": True}
except (TypeError, ValueError):
    DF_WIDTH = {"use_container_width": True}
# --- END styling helpers ---


# --- Simple password gate ---
def check_password():
    """Ask for a password before showing anything else on the page. The
    correct password lives in Streamlit secrets (app_password) rather than
    in this file. Fails closed if that secret is missing (so a blank
    password never gets anyone in), and compares with hmac.compare_digest
    rather than == so the check can't leak timing information."""

    def password_entered():
        correct_password = st.secrets.get("app_password")
        entered_password = st.session_state.get("password_input", "")
        if correct_password and hmac.compare_digest(entered_password, correct_password):
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct"):
        return True

    render_html(
        '<div class="pe-login-head">'
        '<div class="pe-logo">SC</div>'
        '<div class="t">SYComms Command Center</div>'
        '<div class="s">Sign in to view live renewals &amp; sales pipeline data from Zoho CRM.</div>'
        "</div>"
    )
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        with st.container(key="card-login"):
            st.text_input("Password", type="password", on_change=password_entered, key="password_input")
            if st.session_state.get("password_correct") is False:
                st.error("Incorrect password")
    return False


if not check_password():
    st.stop()

# Reserve the hero banner's slot now; it's filled in at the very end of the
# script once the live counts are known (it still appears at the top).
hero_placeholder = st.empty()


def render_hero(target, customer_count, deal_count):
    render_html(
        '<div class="pe-hero"><div>'
        '<div class="pe-eyebrow"><span class="dot"></span> LIVE · ZOHO CRM</div>'
        '<div class="pe-title">SYComms Renewals &amp; Sales <span>Command Center</span></div>'
        '<div class="pe-sub">Contract renewals, new accounts and the live sales pipeline, '
        "straight from Zoho CRM.</div></div>"
        '<div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">'
        + chip(f"{customer_count} customers tracked", "accent")
        + chip(f"{deal_count} deals in pipeline", "accent")
        + chip(f"Last refreshed {datetime.now(UK_TZ).strftime('%H:%M:%S')}")
        + "</div></div>",
        target=target,
    )


# --- Zoho CRM Connection & Loading ---
ZOHO_ACCOUNTS_URL = "https://accounts.zoho.eu/oauth/v2/token"
ZOHO_API_DOMAIN = "https://www.zohoapis.eu"
ACCOUNT_FIELDS = (
    "Account_Name,Account_Type,Tag,Phone,Post_Code,Owner,"
    "Primary_Contact_Name,Primary_Contact_Number,"
    "Contract_Date_End,Contact_Term,Network_Signed,No_of_Handsets"
)

# Accounts are identified primarily by the "Account Type" picklist, but a
# couple of tags need checking too — see the exclusion rules in load_accounts().
ACCOUNT_TYPE = "SYC Customer"

# A "MY PA" tag alone means this isn't a real SYComms customer — but some
# genuine customers carry MY PA *and* SYC together, so only exclude when
# MY PA shows up on its own, without the SYC tag alongside it.
EXCLUDE_UNLESS_ALSO_TAGGED = ("MY PA", "SYC")

# Accounts tagged DEAD ACCOUNT are closed and should never appear here.
DEAD_ACCOUNT_TAG = "DEAD ACCOUNT"

URGENCY_ORDER = ["Red", "Amber", "OK", "Unknown"]
URGENCY_LABEL = {
    "Red": "🔴 Red — under 12 months",
    "Amber": "🟠 Amber — 12–24 months",
    "OK": "🟢 OK — 24+ months",
    "Unknown": "⚪ No end date on file",
}

# Org ID for building direct "open this record in Zoho" links in the tables
# below. Zoho's own record URLs follow this pattern.
ZOHO_ORG_ID = "20098805637"


def zoho_account_url(account_id):
    return f"https://crm.zoho.eu/crm/org{ZOHO_ORG_ID}/tab/Accounts/{account_id}"


def zoho_deal_url(deal_id):
    # Zoho's deal record URLs still use the module's old internal name.
    return f"https://crm.zoho.eu/crm/org{ZOHO_ORG_ID}/tab/Potentials/{deal_id}"


# Deals fields. Monthly_Lease_Spend / Total_Lease_Value / Monthly_Network_Spend
# are the fields this org actually populates when closing a deal (confirmed
# live against a real closed-won deal); Potential_Value / Services_Value sit
# empty, so they're only used as a fallback.
DEAL_FIELDS = (
    "Deal_Name,Owner,Account_Name,Appt_Date_Time,Potential_Value,Services_Value,"
    "Monthly_Lease_Spend,Total_Lease_Value,Monthly_Network_Spend,Stage,Closing_Date,"
    "Created_By,Created_Time"
)
CLOSED_WON_STAGE = "Closed Won"
SOLD_DEALS_WINDOW_DAYS = 30

# This org's Deals module holds both SYComms and SYPLUS business — the only
# thing separating them on the Deal record itself is who owns it. SYComms
# consultants are on @sycomms.co.uk, SYPLUS's on @syplus.co.uk.
SYCOMMS_EMAIL_DOMAIN = "@sycomms.co.uk"

# Sales pipeline stage groupings (matched case-insensitively).
STAGES_EARLY = ["Meeting Booked", "Booked", "2nd Dem", "Pending"]
STAGES_ACTIVE = ["Create Proposal", "Send for Signature", "Negotiations", "On-Hold"]
STAGES_WON = ["Sold", "Closed Won"]
STAGES_LOST = ["Closed Lost", "Not Sold", "Lost", "Unsuccessful"]
STAGE_DOT_COLORS = {
    "sold": "#34D399", "closed won": "#34D399", "2nd dem": "#38D6F5",
    "meeting booked": "#FBBF24", "booked": "#FBBF24", "pending": "#8C98B0",
    "on-hold": "#FB923C", "create proposal": "#7C83FF", "send for signature": "#7C83FF",
    "negotiations": "#34D399", "closed lost": "#F87171", "not sold": "#F87171",
}

ACCENT = "#7C83FF"


def render_leaderboard(series, category_label, y_label):
    """Renders a single-series leaderboard bar chart, sorted highest first.

    Built by hand with Altair rather than st.bar_chart: Streamlit's built-in
    chart types always call Altair's .interactive() under the hood, which
    binds mouse-wheel scrolling over the chart to zoom — so scrolling the
    page while the cursor happens to be over the chart zooms it instead of
    scrolling. Building the same chart without .interactive() keeps normal
    page scrolling working. Styled to match the dark theme."""
    if series.empty:
        st.info("Nothing to show yet.")
        return
    chart_df = series.rename_axis(category_label).reset_index(name=y_label)
    chart = (
        alt.Chart(chart_df)
        .mark_bar(color=ACCENT, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(f"{category_label}:N", sort="-y", title="", axis=alt.Axis(labelAngle=-25)),
            y=alt.Y(f"{y_label}:Q", title=y_label),
            tooltip=[category_label, y_label],
        )
        .properties(height=260)
        .configure(background="transparent")
        .configure_axis(
            labelColor="#8C98B0", titleColor="#8C98B0", gridColor="#1C2740",
            domainColor="#26324D", tickColor="#26324D",
        )
        .configure_view(strokeOpacity=0)
    )
    try:
        st.altair_chart(chart, width="stretch", theme=None)
    except TypeError:
        st.altair_chart(chart, use_container_width=True, theme=None)


def date_range_presets(reference_date):
    """Returns {button label: (start_date, end_date)} for the quick-pick
    shortcuts shown above each date-range picker, all as plain datetime.date
    objects relative to reference_date (normally 'today')."""
    this_month_start = reference_date.replace(day=1)
    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    this_year_start = reference_date.replace(month=1, day=1)
    last_year_end = this_year_start - timedelta(days=1)
    last_year_start = last_year_end.replace(month=1, day=1)
    return {
        "This month": (this_month_start, reference_date),
        "Last month": (last_month_start, last_month_end),
        "This year": (this_year_start, reference_date),
        "Last year": (last_year_start, last_year_end),
    }


def render_date_range_picker(label, key, default_window_days, reference_date):
    """Renders the This month / Last month / This year / Last year shortcut
    buttons plus the manual date-range picker underneath, both writing into
    the same widget (via session_state), so either way of picking a period
    lands in the same place. Returns the chosen (start, end) as a pair of
    pandas Timestamps.

    Clicking a shortcut button sets st.session_state[key] *before* the
    st.date_input with that key is created further down in this same run —
    the supported way to have a button drive another widget's value."""
    presets = date_range_presets(reference_date)
    preset_cols = st.columns(len(presets))
    for col, (preset_label, preset_dates) in zip(preset_cols, presets.items()):
        if col.button(preset_label, key=f"{key}_preset_{preset_label}", **FULL_WIDTH):
            st.session_state[key] = preset_dates

    default_start = reference_date - timedelta(days=default_window_days)
    # Only pass `value=` on the widget's very first run. Once it has a value
    # in session_state, passing `value=` alongside it triggers a (harmless
    # but noisy) Streamlit warning about setting a widget two ways at once.
    date_input_kwargs = {"max_value": reference_date, "key": key}
    if key not in st.session_state:
        date_input_kwargs["value"] = (default_start, reference_date)
    selected_range = st.date_input(label, **date_input_kwargs)
    # Streamlit hands back a single date while a user is still picking the
    # second one in the range picker — fall back to the default range then.
    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        range_start, range_end = selected_range
    else:
        range_start, range_end = default_start, reference_date

    return pd.Timestamp(range_start), pd.Timestamp(range_end)


def add_months(d, delta):
    month_index = d.month - 1 + delta
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


@st.cache_data(ttl=270)  # Zoho access tokens last 1hr; refresh well before that
def get_access_token():
    try:
        creds = st.secrets["zoho"]
    except Exception as err:
        raise RuntimeError(
            f"Missing Zoho credentials in Streamlit secrets. Details: {err}"
        )

    try:
        resp = requests.post(
            ZOHO_ACCOUNTS_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": creds["client_id"],
                "client_secret": creds["client_secret"],
                "refresh_token": creds["refresh_token"],
            },
            timeout=15,
        )
        payload = resp.json()
    except Exception as err:
        raise RuntimeError(f"Could not reach Zoho accounts server. Details: {err}")

    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"Zoho authentication failed: {payload}")
    return token


def _paged_get(path, params, what, quiet=False):
    """Fetches every page of a Zoho module list. Raises a readable error on
    failure unless quiet=True (used for nice-to-have lookups), in which case
    it returns whatever it managed to get."""
    token = get_access_token()
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    records = []
    page = 1
    while True:
        try:
            resp = requests.get(
                f"{ZOHO_API_DOMAIN}/crm/v2/{path}",
                headers=headers,
                params={**params, "per_page": 200, "page": page},
                timeout=20,
            )
        except Exception as err:
            if quiet:
                break
            raise RuntimeError(f"Could not reach Zoho CRM API for {what}. Details: {err}")

        if resp.status_code == 204:
            break  # no data at all
        if resp.status_code != 200:
            if quiet:
                break
            raise RuntimeError(
                f"Zoho CRM API returned an error fetching {what} "
                f"(status {resp.status_code}): {resp.text}"
            )

        payload = resp.json()
        records.extend(payload.get("data", []))
        if not payload.get("info", {}).get("more_records"):
            break
        page += 1
    return records


@st.cache_data(ttl=3600)  # field structure changes rarely, if ever
def get_reseller_field_api_name():
    """The Accounts module's 'Reseller' field API name, looked up by its on-screen label
    (like the Amount lookup below). None if it can't be found, so the app still works without it."""
    try:
        token = get_access_token()
        resp = requests.get(
            f"{ZOHO_API_DOMAIN}/crm/v2/settings/fields",
            headers={"Authorization": f"Zoho-oauthtoken {token}"},
            params={"module": "Accounts"},
            timeout=20,
        )
        if resp.status_code != 200:
            return None
        for field in resp.json().get("fields", []):
            if (field.get("field_label") or "").strip().lower() == "reseller":
                return field.get("api_name")
    except Exception:
        return None
    return None


def reseller_name(value):
    """Picklist (text) or lookup ({name, id}) — either way, just the name."""
    if isinstance(value, dict):
        return (value.get("name") or "").strip()
    return str(value or "").strip()


NO_RESELLER = "No reseller (ours)"


@st.cache_data(ttl=60)
def load_accounts():
    reseller_field = get_reseller_field_api_name()
    fields = ACCOUNT_FIELDS + (f",{reseller_field}" if reseller_field else "")
    records = _paged_get(
        "Accounts",
        {"fields": fields, "sort_by": "Modified_Time", "sort_order": "desc"},
        "Accounts",
    )

    rows = []
    for r in records:
        if (r.get("Account_Type") or "") != ACCOUNT_TYPE:
            continue

        tag_names = [t.get("name", "") for t in (r.get("Tag") or [])]

        if DEAD_ACCOUNT_TAG in tag_names:
            continue  # closed account — never show it

        exclude_tag, unless_tag = EXCLUDE_UNLESS_ALSO_TAGGED
        if exclude_tag in tag_names and unless_tag not in tag_names:
            continue  # MY PA without SYC alongside it — not a real customer

        rows.append(
            {
                "Account ID": r.get("id"),
                "Account Name": r.get("Account_Name") or "",
                "Account Owner": (r.get("Owner") or {}).get("name") or "",
                "Reseller": reseller_name(r.get(reseller_field)) if reseller_field else "",
                "All Tags": ", ".join(sorted(tag_names)),
                "Primary Contact": r.get("Primary_Contact_Name") or "",
                "Primary Contact Number": r.get("Primary_Contact_Number") or "",
                "Phone": r.get("Phone") or "",
                "Postal Code": r.get("Post_Code") or "",
                "Contract Signed": r.get("Network_Signed") or "",
                "Contract Term (months)": r.get("Contact_Term"),
                "Contract End Date": r.get("Contract_Date_End") or "",
                "No. of Handsets": r.get("No_of_Handsets"),
            }
        )

    return pd.DataFrame(rows)


@st.cache_data(ttl=600)  # site contacts change far less often than contract dates
def get_contacts_lookup():
    """Fall back for accounts with no Primary Contact set directly, from their
    linked Contact records. Pulls the whole Contacts module in bulk (a handful
    of paginated requests) rather than one request per account — much faster
    than looking up each account's contacts one at a time. Picks whichever
    linked contact has a mobile or phone number on file (preferring mobile),
    so the number is one someone can actually ring. Contacts are a
    nice-to-have, so any failure here is swallowed rather than sinking the
    whole page."""
    records = _paged_get(
        "Contacts", {"fields": "Account_Name,Full_Name,Phone,Mobile"}, "Contacts", quiet=True
    )

    contacts_by_account_id = {}
    for c in records:
        account = c.get("Account_Name") or {}
        account_id = account.get("id")
        if account_id:
            contacts_by_account_id.setdefault(account_id, []).append(c)

    contacts_by_account = {}
    for account_id, contacts in contacts_by_account_id.items():
        best = next((c for c in contacts if c.get("Mobile")), None)
        if best is None:
            best = next((c for c in contacts if c.get("Phone")), contacts[0])
        contacts_by_account[account_id] = {
            "name": best.get("Full_Name") or "",
            "number": best.get("Mobile") or best.get("Phone") or "",
        }

    return contacts_by_account


# The "Legal Contracts" related list shown on each Account page in Zoho is a
# custom module rather than a plain field, so it needs its own small lookup.
# Its REST API name is "Contracts" — the tab in the CRM's own UI shows it
# internally as "CustomModule4", which is a different, unrelated identifier.
LEGAL_CONTRACTS_MODULE = "Contracts"


@st.cache_data(ttl=3600)  # field structure changes rarely, if ever
def get_amount_field_api_name():
    """Looks up the Amount field's actual Zoho API name by its on-screen
    label, rather than hardcoding it — this org's internal field names don't
    always match what's shown on screen (e.g. 'Contract Signed' is really
    stored as Network_Signed), so this is safer than guessing.

    Returns (api_name_or_None, error_message_or_None) so a permissions
    problem can be shown on the page instead of silently leaving every
    Amount blank."""
    token = get_access_token()
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    try:
        resp = requests.get(
            f"{ZOHO_API_DOMAIN}/crm/v2/settings/fields",
            headers=headers,
            params={"module": LEGAL_CONTRACTS_MODULE},
            timeout=20,
        )
    except Exception as err:
        return None, f"could not reach Zoho ({err})"

    if resp.status_code != 200:
        return None, f"Zoho returned status {resp.status_code}: {resp.text[:200]}"

    for field in resp.json().get("fields", []):
        if (field.get("field_label") or "").strip().lower() == "amount":
            return field.get("api_name"), None
    return None, "no 'Amount' field found on the Legal Contracts module"


@st.cache_data(ttl=300)
def get_legal_contract_amounts(account_ids):
    """Pulls each account's Legal Contracts related list and sums the Amount
    field. Only ever called for the small handful of accounts in the New
    Accounts Added list, so one request per account is fine here — this
    isn't the hundreds-of-accounts case the Contacts lookup had to avoid.
    Cached, so clicking around the page doesn't re-fire these requests.

    Returns (amounts_by_account_id, first_error_or_None)."""
    amount_field, field_error = get_amount_field_api_name()
    if not amount_field:
        return {}, field_error
    if not account_ids:
        return {}, None

    token = get_access_token()
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    amounts = {}
    first_error = None
    for account_id in account_ids:
        try:
            resp = requests.get(
                f"{ZOHO_API_DOMAIN}/crm/v2/Accounts/{account_id}/{LEGAL_CONTRACTS_MODULE}",
                headers=headers,
                params={"fields": amount_field},
                timeout=20,
            )
        except Exception as err:
            first_error = first_error or f"could not reach Zoho ({err})"
            continue

        if resp.status_code == 204:
            continue  # no legal contracts on file for this account
        if resp.status_code != 200:
            first_error = first_error or f"Zoho returned status {resp.status_code}: {resp.text[:200]}"
            continue

        total = 0
        for record in resp.json().get("data", []):
            value = record.get(amount_field)
            if isinstance(value, (int, float)):
                total += value
        amounts[account_id] = total

    return amounts, first_error


def parse_appt(raw):
    """Zoho returns the appointment as ISO 8601 with a timezone offset (e.g.
    2026-09-10T14:00:00+01:00). Converted to UK local time, so a visit shows
    on the right day and hour whatever the server's own clock is set to."""
    if not raw:
        return pd.NaT
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is not None:
            dt = dt.astimezone(UK_TZ).replace(tzinfo=None)
        return pd.Timestamp(dt)
    except ValueError:
        return pd.to_datetime(raw, errors="coerce", dayfirst=True)


@st.cache_data(ttl=60)
def load_deals():
    """Every deal, once, from the Deals module. The Sales Pipeline cards use
    the SYComms-owned slice of it; the Sold Deals card uses the Closed Won
    slice."""
    records = _paged_get(
        "Deals",
        {"fields": DEAL_FIELDS, "sort_by": "Modified_Time", "sort_order": "desc"},
        "Deals",
    )

    rows = []
    for r in records:
        owner = r.get("Owner") or {}
        account = r.get("Account_Name") or {}
        lease_total = float(r.get("Total_Lease_Value") or 0) or float(r.get("Potential_Value") or 0)
        network_monthly = float(r.get("Monthly_Network_Spend") or 0) or float(r.get("Services_Value") or 0)
        rows.append(
            {
                "Deal ID": r.get("id"),
                "Client Name": r.get("Deal_Name") or "",
                "Account Name": account.get("name") or "",
                "Sales Rep": owner.get("name") or "Unassigned",
                "Owner Email": (owner.get("email") or "").lower(),
                "Parsed Date": parse_appt(r.get("Appt_Date_Time")),
                "Status": r.get("Stage") or "",
                "Closing Date": r.get("Closing_Date") or "",
                "Monthly Lease Spend": float(r.get("Monthly_Lease_Spend") or 0),
                "Total Lease Value": lease_total,
                "Monthly Network Spend": network_monthly,
                "Created By": (r.get("Created_By") or {}).get("name") or "",
                "Created By Email": ((r.get("Created_By") or {}).get("email") or "").lower(),
                "Created Time": parse_appt(r.get("Created_Time")),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(
            columns=[
                "Deal ID", "Client Name", "Account Name", "Sales Rep", "Owner Email",
                "Parsed Date", "Status", "Closing Date", "Monthly Lease Spend",
                "Total Lease Value", "Monthly Network Spend",
                "Created By", "Created By Email", "Created Time",
            ]
        )
    df["Parsed Date"] = pd.to_datetime(df["Parsed Date"], errors="coerce")
    df["Created Time"] = pd.to_datetime(df["Created Time"], errors="coerce")
    return df


# --- Load & Error Handling ---
try:
    df = load_accounts()
except Exception as e:
    st.error(f"🚨 Zoho CRM Connection Error: {e}")
    st.stop()

if df.empty:
    st.warning(
        f"No accounts with Account Type = **{ACCOUNT_TYPE}** were found in Zoho."
    )
    st.stop()

# The deals feed only powers the Sales Pipeline tab, so a problem there
# shouldn't take the Renewals tab down with it — it's reported inside that tab.
try:
    deals_df = load_deals()
    deals_error = None
except Exception as e:
    deals_df = pd.DataFrame()
    deals_error = str(e)

# Fill in a site contact for any account with no Primary Contact set directly
# on the Account record, from that account's linked Contact records.
try:
    contacts_lookup = get_contacts_lookup()
except Exception:
    contacts_lookup = {}

needs_lookup = df["Primary Contact"] == ""
for account_id, contact in contacts_lookup.items():
    mask = needs_lookup & (df["Account ID"] == account_id)
    df.loc[mask, "Primary Contact"] = contact["name"]
    df.loc[mask, "Primary Contact Number"] = contact["number"]

df["Open in Zoho"] = df["Account ID"].apply(zoho_account_url)


# --- Data Prep: contract end date, time remaining, urgency ---
def parse_zoho_date(value):
    """Zoho returns Contract End Date as a formula-driven string, and the
    signed date as a plain date string. Both use ISO-style yyyy-MM-dd."""
    if not value:
        return pd.NaT
    try:
        return pd.to_datetime(value, errors="coerce")
    except Exception:
        return pd.NaT


df["Contract End Date"] = df["Contract End Date"].apply(parse_zoho_date)
now_uk = datetime.now(UK_TZ).replace(tzinfo=None)
today = pd.Timestamp(now_uk.date())
df["Days Remaining"] = (df["Contract End Date"] - today).dt.days


def urgency_tier(days):
    if pd.isna(days):
        return "Unknown"
    if days <= 365:  # includes contracts already ended
        return "Red"
    if days <= 730:
        return "Amber"
    return "OK"


def time_remaining_label(days):
    if pd.isna(days):
        return "No end date on file"
    days = int(days)
    if days < 0:
        return f"Overdue by {abs(days) // 30} mo" if abs(days) >= 30 else f"Overdue by {abs(days)}d"
    years, rem_days = divmod(days, 365)
    months = rem_days // 30
    if years == 0 and months == 0:
        return f"{days}d left"
    parts = []
    if years:
        parts.append(f"{years}y")
    if months:
        parts.append(f"{months}m")
    return " ".join(parts) + " left"


df["Urgency"] = df["Days Remaining"].apply(urgency_tier)
df["Time Remaining"] = df["Days Remaining"].apply(time_remaining_label)


def is_rolling_contract(term):
    """Rolling contracts are marked with a contract term of exactly 12
    months — a fixed reference value, not a genuine 'expiring soon' date."""
    try:
        return int(term) == 12
    except (TypeError, ValueError):
        return False


df["Rolling Contract"] = df["Contract Term (months)"].apply(is_rolling_contract)


def format_handsets(value):
    if pd.isna(value):
        return "None"
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return "None"


# New deals — contract signed within the last 30 days — flagged up front so
# they can be handed to billing for onboarding without digging for them.
NEW_DEAL_WINDOW_DAYS = 30
df["Contract Signed Date"] = df["Contract Signed"].apply(parse_zoho_date)
df["Days Since Signed"] = (today - df["Contract Signed Date"]).dt.days
df["New Deal"] = df["Days Since Signed"].apply(
    lambda d: pd.notna(d) and 0 <= d <= NEW_DEAL_WINDOW_DAYS
)


def days_since_label(days):
    if pd.isna(days):
        return "Unknown"
    days = int(days)
    if days == 0:
        return "Signed today"
    if days == 1:
        return "Signed yesterday"
    return f"Signed {days} days ago"


# --- Sidebar: brand, live snapshot, refresh, log out ---
render_html(
    '<div class="pe-brand"><div class="pe-logo">SC</div><div>'
    '<div class="name">SYComms</div><div class="tag">Renewals &amp; Sales Command Center</div>'
    "</div></div>",
    target=st.sidebar,
)
render_html(
    '<div class="pe-status-row"><span class="dot"></span> Connected to Zoho CRM</div>',
    target=st.sidebar,
)

# --- Reseller filter (sidebar): blank = our own customers, or a reseller such as FT Security Systems ---
df["Reseller"] = df.get("Reseller", pd.Series("", index=df.index)).fillna("").replace("", NO_RESELLER)
reseller_options = [NO_RESELLER] + sorted(r for r in df["Reseller"].unique() if r != NO_RESELLER)
if "reseller_filter" not in st.session_state:
    st.session_state["reseller_filter"] = list(reseller_options)  # Everyone, until someone narrows it
else:  # Keep the choice, dropping any option that no longer exists
    st.session_state["reseller_filter"] = [r for r in st.session_state["reseller_filter"] if r in reseller_options]
selected_resellers = st.sidebar.multiselect(
    "Reseller", reseller_options, key="reseller_filter",
    help="Whose customers to show. 'No reseller (ours)' is accounts with the Reseller field blank in Zoho.",
)
if not get_reseller_field_api_name():
    st.sidebar.caption("⚠️ Couldn't find a 'Reseller' field on Accounts in Zoho, so every account shows as ours.")
df = df[df["Reseller"].isin(selected_resellers)].copy()
reseller_label = ("All resellers" if len(selected_resellers) == len(reseller_options)
                  else ", ".join(selected_resellers) or "none selected")

render_html(
    '<div class="pe-mini-grid">'
    f'<div class="pe-mini"><div class="l">Customers</div><div class="v">{len(df)}</div></div>'
    f'<div class="pe-mini"><div class="l">Red</div><div class="v">{int(((df["Urgency"] == "Red") & (~df["Rolling Contract"])).sum())}</div></div>'
    f'<div class="pe-mini"><div class="l">Amber</div><div class="v">{int((df["Urgency"] == "Amber").sum())}</div></div>'
    f'<div class="pe-mini"><div class="l">New (30d)</div><div class="v">{int(df["New Deal"].sum())}</div></div>'
    "</div>",
    target=st.sidebar,
)

if st.sidebar.button("Refresh data now", type="primary", **FULL_WIDTH):
    # Pull fresh data within this same session — a browser refresh (F5) would
    # start a brand-new session and force the password to be re-entered, so
    # this button re-runs the app in place instead, staying logged in.
    st.cache_data.clear()
    st.rerun()
pdf_slot = st.sidebar.empty()  # the PDF download button is placed here at the end of the script
st.sidebar.caption(f"Last refreshed: {datetime.now(UK_TZ).strftime('%d/%m/%Y %H:%M:%S')}")
st.sidebar.caption(
    "Data refreshes from Zoho CRM automatically every 60 seconds, or instantly "
    "with the button above."
)
# --- Zoho token helper: only appears when `show_token_helper = true` is added to the Streamlit secrets ---
def _secret_flag(*places):
    """True when `show_token_helper` is switched on in Secrets - at the top level, or (if it ended up under the
    [zoho] heading by mistake) in there. Accepts true / "true" / "yes" / 1."""
    for place in places:
        try:
            value = place.get("show_token_helper") if place is not None else None
        except Exception:
            value = None
        if value is not None and str(value).strip().lower() in ("true", "1", "yes", "on"):
            return True
    return False


try:
    _show_token_helper = _secret_flag(st.secrets, st.secrets.get("zoho"))
except Exception:
    _show_token_helper = False
if _show_token_helper:
    with st.sidebar.expander("Zoho token helper"):
        st.caption(
            "1) In the Zoho API Console (api-console.zoho.eu) open your Self Client, Generate Code with scopes "
            "ZohoCRM.modules.ALL,ZohoCRM.settings.ALL,ZohoCRM.users.READ (10 minutes). "
            "2) Paste the code below straight away - it works once. "
            "3) Copy the refresh token it shows into the app's Secrets under [zoho]."
        )
        if st.button("Check what the current token can do", key="zoho_check_scopes", **FULL_WIDTH):
            try:
                _c = st.secrets["zoho"]
                _r = requests.post(
                    ZOHO_ACCOUNTS_URL,
                    data={"grant_type": "refresh_token", "client_id": _c["client_id"],
                          "client_secret": _c["client_secret"], "refresh_token": _c["refresh_token"]},
                    timeout=20,
                ).json()
                if _r.get("access_token"):
                    _granted = _r.get("scope", "")
                    st.caption(f"This token's scopes: {_granted or '(Zoho did not list any)'}")
                    _g = _granted.replace(" ", ",").split(",")
                    _has = lambda *names: any(n in _g for n in names)
                    st.write(("✅" if _has("ZohoCRM.modules.ALL", "ZohoCRM.modules.leads.READ", "ZohoCRM.modules.leads.ALL") else "❌") + " Can read Leads")
                    st.write(("✅" if _has("ZohoCRM.users.READ", "ZohoCRM.users.ALL") else "❌") + " Can read the user list")
                    st.write(("✅" if _has("ZohoCRM.settings.ALL", "ZohoCRM.settings.fields.READ") else "❌") + " Can read field settings")
                else:
                    st.error(f"Zoho refused the saved refresh token: {_r.get('error', _r)}")
            except Exception as _err:
                st.error(f"Couldn't check: {_err}")
        _grant = st.text_input("Grant code", key="zoho_grant_code", type="password")
        if st.button("Get refresh token", key="zoho_get_rt", **FULL_WIDTH):
            st.session_state.pop("zoho_new_rt", None)
            try:
                _creds = st.secrets["zoho"]
                _resp = requests.post(
                    ZOHO_ACCOUNTS_URL,
                    data={
                        "grant_type": "authorization_code",
                        "client_id": _creds["client_id"],
                        "client_secret": _creds["client_secret"],
                        "code": _grant.strip(),
                    },
                    timeout=20,
                )
                _payload = _resp.json()
                if _payload.get("refresh_token"):
                    st.session_state["zoho_new_rt"] = (_payload["refresh_token"], _payload.get("scope", ""))
                else:
                    st.error(f"Zoho said: {_payload.get('error', _payload)}. Make a fresh code and try again straight away.")
            except Exception as _err:
                st.error(f"Couldn't reach Zoho: {_err}")
        if st.session_state.get("zoho_new_rt"):
            _rt, _scope = st.session_state["zoho_new_rt"]
            st.success("Done - copy this into Secrets as refresh_token under [zoho], then save.")
            st.code(_rt, language=None)
            if _scope:
                st.caption(f"Scopes granted: {_scope}")
            st.caption("Afterwards remove show_token_helper from Secrets, so this box disappears.")

st.sidebar.divider()
if st.sidebar.button("Log out", **FULL_WIDTH):
    st.session_state["password_correct"] = False
    st.rerun()

tab_renewals, tab_sales, tab_assess = st.tabs(["Renewals", "Sales Pipeline", "Assessment"])

# Filled in as each card renders; the PDF briefing is built from this.
report = {}


# =====================================================================
# TAB 1 — RENEWALS
# =====================================================================
with tab_renewals:

    # --- 1. Overview: filters + top-line KPIs ---
    with st.container(key="card-ren-overview"):
        section_header(1, "Renewals Overview", "Live counts across your SYC Customer accounts")

        filter_cols = st.columns([2, 1])
        selected_urgency = filter_cols[0].multiselect(
            "Urgency",
            options=URGENCY_ORDER,
            default=["Red", "Amber", "Unknown"],
            format_func=lambda u: URGENCY_LABEL[u],
            key="ren_urgency",
            help="Accounts with 24+ months left are hidden by default — add OK to bring them back into view.",
        )
        name_search = filter_cols[1].text_input("Search account name", key="ren_search", placeholder="Type part of a name…")

        filtered_df = df[df["Urgency"].isin(selected_urgency)]
        if name_search:
            filtered_df = filtered_df[
                filtered_df["Account Name"].str.contains(name_search, case=False, na=False)
            ]

        # Rolling contract customers get their own list further down, regardless
        # of the Urgency filter — their contract term is a rolling 12-month
        # marker rather than a genuine countdown, so being caught by the Red
        # filter (or hidden by unticking it) isn't meaningful the way it is for
        # everyone else.
        name_filtered_df = df
        if name_search:
            name_filtered_df = name_filtered_df[
                name_filtered_df["Account Name"].str.contains(name_search, case=False, na=False)
            ]
        rolling_df = name_filtered_df[name_filtered_df["Rolling Contract"]].sort_values("Days Remaining")

        kpi_cols = st.columns(6)
        tiles = [
            ("Customers Tracked", len(df), "renewal-watchlist", ""),
            ("Red (< 12 months)", len(df[(df["Urgency"] == "Red") & (~df["Rolling Contract"])]), "renewal-watchlist", "bad"),
            ("Amber (12–24 months)", len(df[df["Urgency"] == "Amber"]), "renewal-watchlist", "warn"),
            ("No End Date", len(df[df["Urgency"] == "Unknown"]), "no-end-date-list", "muted"),
            ("Rolling Contracts", len(df[df["Rolling Contract"]]), "rolling-section", "cyan"),
            ("New Accounts (30d)", len(df[df["New Deal"]]), "new-accounts-section", "good"),
        ]
        for col, (label, value, anchor, tone) in zip(kpi_cols, tiles):
            with col:
                render_html(kpi_tile(label, value, href=anchor, tone=tone))
        report["ren_tiles"] = tiles
        report["ren_filters"] = (
            f"Reseller: {reseller_label}  -  "
            + "Urgency: " + (", ".join(selected_urgency) if selected_urgency else "none selected")
            + (f"  -  Search: {name_search}" if name_search else "")
        )

    # --- 2. New Accounts Added ---
    with st.container(key="card-ren-new"):
        section_header(
            2, "New Accounts Added",
            "Contracts signed in the chosen period — flag these to billing for onboarding.",
            anchor_id="new-accounts-section",
        )

        range_start_ts, range_end_ts = render_date_range_picker(
            "Show accounts signed between",
            key="new_deals_date_range",
            default_window_days=NEW_DEAL_WINDOW_DAYS,
            reference_date=today.date(),
        )

        report["new_range"] = (range_start_ts, range_end_ts)
        st.caption(
            f"Contracts signed from {range_start_ts.strftime('%d/%m/%Y')} to "
            f"{range_end_ts.strftime('%d/%m/%Y')}."
        )

        # New deals also sit outside the Urgency filter — a freshly signed
        # contract is worth surfacing regardless of how far off its renewal is.
        new_deals_df = name_filtered_df[
            name_filtered_df["Contract Signed Date"].between(range_start_ts, range_end_ts)
        ].sort_values("Contract Signed Date", ascending=False)

        if new_deals_df.empty:
            st.info("No contracts signed in the selected date range.")
        else:
            try:
                legal_contract_amounts, amounts_error = get_legal_contract_amounts(
                    tuple(new_deals_df["Account ID"])
                )
            except Exception as err:
                legal_contract_amounts, amounts_error = {}, str(err)

            if amounts_error:
                st.warning(
                    "⚠️ Couldn't read the Legal Contracts amounts from Zoho, so the Amount "
                    f"column shows “—” for now. Details: {amounts_error}"
                )

            new_deals_display_df = new_deals_df[
                ["Account Name", "Account Owner", "Contract Signed Date", "All Tags", "Open in Zoho"]
            ].copy()
            new_deals_display_df["Contract Signed Date"] = new_deals_df["Days Since Signed"].apply(
                days_since_label
            )
            new_deals_display_df["Amount"] = new_deals_df["Account ID"].apply(
                lambda acc_id: legal_contract_amounts.get(acc_id)
            )
            new_deals_display_df = new_deals_display_df[
                ["Account Name", "Account Owner", "Contract Signed Date", "Amount", "All Tags", "Open in Zoho"]
            ]

            total_amount = sum(v for v in new_deals_display_df["Amount"] if pd.notna(v))
            report["new_table"] = new_deals_display_df.copy()
            report["new_total"] = total_amount
            report["new_amounts_error"] = amounts_error
            new_deals_display_df["Amount"] = new_deals_display_df["Amount"].apply(
                lambda v: f"£{v:,.2f}" if pd.notna(v) else "—"
            )

            st.dataframe(
                new_deals_display_df,
                hide_index=True,
                **DF_WIDTH,
                column_config={"Open in Zoho": st.column_config.LinkColumn(display_text="Open ↗")},
            )
            # Show the selected period as a proper month name when it lines up
            # with one calendar month (the common case), otherwise fall back to
            # showing the actual date range picked above.
            if (
                range_start_ts.year == range_end_ts.year
                and range_start_ts.month == range_end_ts.month
            ):
                period_label = range_start_ts.strftime("%B %Y")
            else:
                period_label = (
                    f"{range_start_ts.strftime('%d %b %Y')} – {range_end_ts.strftime('%d %b %Y')}"
                )
            report["new_period"] = period_label
            st.metric(f"Total service value ({period_label})", f"£{total_amount:,.2f}")

            st.caption("Leaderboard — accounts added per consultant")
            owner_counts = (
                new_deals_df["Account Owner"]
                .replace("", "Unassigned")
                .value_counts()
                .sort_values(ascending=False)
            )
            report["new_owner_counts"] = owner_counts
            render_leaderboard(owner_counts, "Consultant", "Accounts added")

    # --- 3. Renewal Watchlist ---
    with st.container(key="card-ren-list"):
        section_header(
            3, "Renewal Watchlist",
            "Accounts ranked by how soon their contract runs out, soonest first.",
            anchor_id="renewal-watchlist",
        )

        visible_df = filtered_df[
            (filtered_df["Urgency"] != "Unknown") & (~filtered_df["Rolling Contract"])
        ].sort_values("Days Remaining")
        report["ren_visible"] = visible_df
        report["rolling_df"] = rolling_df

        table_cols = [
            "Account Name",
            "Urgency",
            "Time Remaining",
            "Contract End Date",
            "Postal Code",
            "Primary Contact",
            "Primary Contact Number",
            "No. of Handsets",
            "All Tags",
            "Open in Zoho",
        ]

        if visible_df.empty:
            st.info("No accounts match the current filters.")
        else:
            display_df = visible_df[table_cols].copy()
            display_df["Contract End Date"] = display_df["Contract End Date"].dt.strftime("%d/%m/%Y")
            display_df["Urgency"] = display_df["Urgency"].map(URGENCY_LABEL)
            display_df["No. of Handsets"] = display_df["No. of Handsets"].apply(format_handsets)

            def highlight_urgency(row):
                color = {
                    "Red": "background-color: rgba(248, 113, 113, 0.18)",
                    "Amber": "background-color: rgba(251, 191, 36, 0.14)",
                }.get(visible_df.loc[row.name, "Urgency"], "")
                return [color] * len(row)

            st.dataframe(
                display_df.style.apply(highlight_urgency, axis=1),
                hide_index=True,
                **DF_WIDTH,
                column_config={"Open in Zoho": st.column_config.LinkColumn(display_text="Open ↗")},
            )

        # Accounts with no contract end date on file — listed separately rather
        # than mixed in (or silently dropped from) the coloured watchlist above.
        # Rolling contract accounts are excluded here too since they get their
        # own section below instead.
        render_html('<div id="no-end-date-list" class="pe-anchor"></div>')
        unknown_df = filtered_df[
            (filtered_df["Urgency"] == "Unknown") & (~filtered_df["Rolling Contract"])
        ]
        if not unknown_df.empty:
            with st.expander(f"{len(unknown_df)} account(s) with no contract end date on file"):
                st.dataframe(
                    unknown_df[
                        [
                            "Account Name",
                            "Primary Contact",
                            "Primary Contact Number",
                            "Contract Term (months)",
                            "All Tags",
                            "Open in Zoho",
                        ]
                    ],
                    hide_index=True,
                    **DF_WIDTH,
                    column_config={"Open in Zoho": st.column_config.LinkColumn(display_text="Open ↗")},
                )

    # --- 4. Rolling Contract Customers ---
    # Rolling contract customers ("Contract Term (months)" == exactly 12) aren't
    # on a genuine fixed end date, so being flagged Red in the main list above
    # would be misleading — they get their own list here instead, still visible,
    # just kept separate from the "actually expiring soon" watchlist.
    with st.container(key="card-ren-rolling"):
        section_header(
            4, "Rolling Contract Customers",
            "Accounts on a rolling 12-month term. Shown here rather than flagged Red above, "
            "since their renewal date isn't a genuine deadline.",
            anchor_id="rolling-section",
        )

        rolling_table_cols = [
            "Account Name",
            "Time Remaining",
            "Contract End Date",
            "Postal Code",
            "Primary Contact",
            "Primary Contact Number",
            "No. of Handsets",
            "All Tags",
            "Open in Zoho",
        ]

        if rolling_df.empty:
            st.info("No rolling contract accounts match the current filters.")
        else:
            rolling_display_df = rolling_df[rolling_table_cols].copy()
            rolling_display_df["Contract End Date"] = rolling_display_df["Contract End Date"].apply(
                lambda d: d.strftime("%d/%m/%Y") if pd.notna(d) else "No end date on file"
            )
            rolling_display_df["No. of Handsets"] = rolling_display_df["No. of Handsets"].apply(format_handsets)

            st.dataframe(
                rolling_display_df,
                hide_index=True,
                **DF_WIDTH,
                column_config={"Open in Zoho": st.column_config.LinkColumn(display_text="Open ↗")},
            )


# =====================================================================
# TAB 2 — SALES PIPELINE
# =====================================================================
def stage_in(series, names):
    return series.astype(str).str.lower().isin([n.lower() for n in names])


def money(v):
    return f"£{v:,.2f}"


with tab_sales:
    if deals_error:
        st.error(f"🚨 Could not load deals from Zoho: {deals_error}")
        pipeline_df = pd.DataFrame(
            {
                "Deal ID": pd.Series(dtype=str), "Client Name": pd.Series(dtype=str),
                "Sales Rep": pd.Series(dtype=str), "Status": pd.Series(dtype=str),
                "Parsed Date": pd.to_datetime(pd.Series([], dtype="object")),
                "Total Lease Value": pd.Series(dtype=float), "Monthly Network Spend": pd.Series(dtype=float),
            }
        )
        sold_source_df = pd.DataFrame()
        pipeline_filtered_df = pipeline_df
    else:
        # SYComms only — a deal with no owner, or an owner outside
        # sycomms.co.uk (SYPLUS, or an unrelated partner email), doesn't belong
        # on the SYComms pipeline.
        pipeline_df = deals_df[deals_df["Owner Email"].str.endswith(SYCOMMS_EMAIL_DOMAIN.lower())].copy()
        sold_source_df = deals_df

    current_date = now_uk

    # --- 1. Pipeline Overview: timeframe + filters + KPIs ---
    with st.container(key="card-sp-overview"):
        section_header(
            1, "Pipeline Overview",
            "SYComms deals by appointment date — choose a timeframe, then narrow by consultant or stage.",
        )

        timeframe_options = ["Specific Month", "Month-to-Date (MTD)", "Quarterly", "Yearly", "All Time"]
        tf_cols = st.columns([1.2, 1, 1, 1.1])  # timeframe, then its month/quarter/year picker(s)
        timeframe_option = tf_cols[0].selectbox(
            "Timeframe view", timeframe_options, index=0, key="sp_timeframe"
        )

        time_filtered_df = pipeline_df.copy()
        timeframe_label = "All time"
        year_options = [current_date.year, current_date.year - 1, current_date.year - 2]

        if timeframe_option == "Month-to-Date (MTD)":
            timeframe_label = current_date.strftime("%B %Y") + " (month to date)"
            time_filtered_df = time_filtered_df[
                (time_filtered_df["Parsed Date"].dt.year == current_date.year)
                & (time_filtered_df["Parsed Date"].dt.month == current_date.month)
                & (time_filtered_df["Parsed Date"] <= pd.Timestamp(current_date))
            ]
        elif timeframe_option == "Specific Month":
            valid_dates = pipeline_df["Parsed Date"].dropna()
            if not valid_dates.empty:
                available_months = (
                    valid_dates.dt.to_period("M").drop_duplicates().sort_values(ascending=False)
                )
                month_str_options = [m.to_timestamp().strftime("%B %Y") for m in available_months]
            else:
                month_str_options = [current_date.strftime("%B %Y")]
            current_month_str = current_date.strftime("%B %Y")
            default_index = (
                month_str_options.index(current_month_str)
                if current_month_str in month_str_options
                else 0
            )
            selected_month_str = tf_cols[1].selectbox(
                "Month", month_str_options, index=default_index, key="sp_month"
            )
            chosen_period = pd.to_datetime(selected_month_str, format="%B %Y")
            timeframe_label = selected_month_str
            time_filtered_df = time_filtered_df[
                (time_filtered_df["Parsed Date"].dt.year == chosen_period.year)
                & (time_filtered_df["Parsed Date"].dt.month == chosen_period.month)
            ]
        elif timeframe_option == "Quarterly":
            current_quarter = (current_date.month - 1) // 3 + 1
            selected_q = tf_cols[1].selectbox("Quarter", [1, 2, 3, 4], index=current_quarter - 1, key="sp_quarter")
            selected_year = tf_cols[2].selectbox("Year", year_options, key="sp_q_year")
            timeframe_label = f"Q{selected_q} {selected_year}"
            time_filtered_df = time_filtered_df[
                (time_filtered_df["Parsed Date"].dt.year == selected_year)
                & (time_filtered_df["Parsed Date"].dt.quarter == selected_q)
            ]
        elif timeframe_option == "Yearly":
            selected_year = tf_cols[1].selectbox("Year", year_options, key="sp_year")
            timeframe_label = str(selected_year)
            time_filtered_df = time_filtered_df[time_filtered_df["Parsed Date"].dt.year == selected_year]

        # Consultant & stage filters (options come from what's in the chosen timeframe)
        rep_options = ["All"] + sorted(time_filtered_df["Sales Rep"].unique()) if not time_filtered_df.empty else ["All"]
        status_options = ["All"] + sorted(s for s in time_filtered_df["Status"].unique() if s) if not time_filtered_df.empty else ["All"]
        filter_row = st.columns([1.2, 1, 1, 1.1])
        selected_rep = filter_row[0].selectbox("Consultant", rep_options, key="sp_rep")
        selected_status = filter_row[1].selectbox("Stage", status_options, key="sp_status")
        show_financials = filter_row[2].toggle("Show financials", value=False, key="sp_financials")

        pipeline_filtered_df = time_filtered_df.copy()
        if selected_rep != "All":
            pipeline_filtered_df = pipeline_filtered_df[pipeline_filtered_df["Sales Rep"] == selected_rep]
        if selected_status != "All":
            pipeline_filtered_df = pipeline_filtered_df[pipeline_filtered_df["Status"] == selected_status]

        def count_stages(frame, stages):
            return 0 if frame.empty else int(stage_in(frame["Status"], stages).sum())

        total_deals_count = len(pipeline_filtered_df)
        early_count = count_stages(pipeline_filtered_df, STAGES_EARLY)
        active_count = count_stages(pipeline_filtered_df, STAGES_ACTIVE)
        won_count = count_stages(pipeline_filtered_df, STAGES_WON)
        lost_count = count_stages(pipeline_filtered_df, STAGES_LOST)

        pk = st.columns(4)
        with pk[0]:
            render_html(kpi_tile("Deals in view", total_deals_count))
        with pk[1]:
            render_html(kpi_tile("New / booked appointments", early_count, tone="warn"))
        with pk[2]:
            render_html(kpi_tile("In progress / closing", active_count, tone="cyan"))
        with pk[3]:
            render_html(kpi_tile("Won / closed", f"{won_count} won · {lost_count} lost", tone="good"))

        sales_report = {
            "timeframe": timeframe_label, "rep": selected_rep, "status": selected_status,
            "total": total_deals_count, "early": early_count, "active": active_count,
            "won": won_count, "lost": lost_count, "show_fin": show_financials,
            "upcoming": None, "rep_summary": None, "won_by_rep": pd.Series(dtype=int), "stages": [],
        }
        if not deals_error:
            report["sales"] = sales_report

        if show_financials:
            st.caption(
                "Financials use each deal's Total Lease Value and Monthly Network Spend "
                "(the fields filled in when a deal is closed)."
            )
            won_mask = stage_in(pipeline_filtered_df["Status"], STAGES_WON) if not pipeline_filtered_df.empty else pd.Series(dtype=bool)
            sales_report["fin_pipeline"] = float(pipeline_filtered_df["Total Lease Value"].sum())
            sales_report["fin_won"] = float(pipeline_filtered_df.loc[won_mask, "Total Lease Value"].sum())
            sales_report["fin_network"] = float(pipeline_filtered_df.loc[won_mask, "Monthly Network Spend"].sum())
            fk = st.columns(3)
            with fk[0]:
                render_html(kpi_tile("Pipeline lease value", money(pipeline_filtered_df["Total Lease Value"].sum())))
            with fk[1]:
                render_html(kpi_tile("Won lease value", money(pipeline_filtered_df.loc[won_mask, "Total Lease Value"].sum()), tone="good"))
            with fk[2]:
                render_html(kpi_tile("Won monthly network spend", money(pipeline_filtered_df.loc[won_mask, "Monthly Network Spend"].sum()), tone="good"))

    # --- 2. Pipeline Schedule ---
    with st.container(key="card-sp-schedule"):
        section_header(
            2, "Pipeline Schedule",
            f"Deals and their stage, soonest appointment first ({timeframe_option}).",
        )
        if pipeline_filtered_df.empty:
            st.info("No records found matching your selected timeframe and filters.")
        else:
            sched = pipeline_filtered_df.sort_values("Parsed Date", ascending=True).copy()
            sched["Appointment"] = sched["Parsed Date"].apply(
                lambda d: d.strftime("%d/%m/%Y %H:%M") if pd.notna(d) else "No appointment date"
            )
            sched["Open in Zoho"] = sched["Deal ID"].apply(zoho_deal_url)
            sched_cols = ["Appointment", "Client Name", "Sales Rep", "Status"]
            if show_financials:
                sched["Total Lease Value"] = sched["Total Lease Value"].apply(money)
                sched["Monthly Network Spend"] = sched["Monthly Network Spend"].apply(money)
                sched_cols += ["Total Lease Value", "Monthly Network Spend"]
            sched_cols.append("Open in Zoho")
            st.dataframe(
                sched[sched_cols],
                **DF_WIDTH,
                hide_index=True,
                column_config={"Open in Zoho": st.column_config.LinkColumn(display_text="Open ↗")},
            )

    # --- 3. Diary ---
    with st.container(key="card-sp-diary"):
        section_header(
            3, "Diary — Booked Appointments",
            "Every deal with an appointment date on file. Follows the consultant and stage filters "
            "above, but not the timeframe — so you can page back and forward freely.",
            anchor_id="sp-diary-section",
        )

        diary_source = pipeline_df
        if selected_rep != "All":
            diary_source = diary_source[diary_source["Sales Rep"] == selected_rep]
        if selected_status != "All":
            diary_source = diary_source[diary_source["Status"] == selected_status]

        sales_report["upcoming"] = (
            diary_source[diary_source["Parsed Date"] >= today].sort_values("Parsed Date").head(10)
        )

        appointments = []
        for _, row in diary_source.iterrows():
            if pd.notna(row["Parsed Date"]):
                appointments.append(
                    {
                        "deal_id": row.get("Deal ID"),
                        "client_name": row["Client Name"],
                        "consultant": row["Sales Rep"],
                        "status": row["Status"] or "Unknown",
                        "date": row["Parsed Date"].date().isoformat(),
                        "time": row["Parsed Date"].strftime("%H:%M"),
                    }
                )

        appointments_by_date = {}
        for appt in appointments:
            appointments_by_date.setdefault(appt["date"], []).append(appt)
        for day_appts in appointments_by_date.values():
            day_appts.sort(key=lambda a: a["time"])

        def render_diary_appointment(appt):
            """One diary entry: time, client, consultant and stage."""
            with st.container(key=f"appt-{appt['deal_id']}"):
                deal_link = zoho_deal_url(appt["deal_id"]) if appt["deal_id"] else None
                client_label = f"[{appt['client_name']}]({deal_link})" if deal_link else appt["client_name"]
                st.markdown(f"**{appt['time']}** — {client_label}")
                color = STAGE_DOT_COLORS.get(appt["status"].lower(), "#8C98B0")
                st.markdown(
                    f"👤 {esc(appt['consultant'])} &nbsp;·&nbsp; "
                    f"<span style='color:{color}'>●</span> {esc(appt['status'])}",
                    unsafe_allow_html=True,
                )

        if "diary_ref_date" not in st.session_state:
            st.session_state["diary_ref_date"] = date.today()

        diary_view_mode = st.radio("View", options=["Week", "Month"], horizontal=True, key="diary_view_mode")

        nav_cols = st.columns([1, 1, 1, 4])
        if nav_cols[0].button("Previous", key="sp_diary_prev", **FULL_WIDTH):
            if diary_view_mode == "Week":
                st.session_state["diary_ref_date"] -= timedelta(days=7)
            else:
                st.session_state["diary_ref_date"] = add_months(st.session_state["diary_ref_date"], -1)
        if nav_cols[1].button("Today", key="sp_diary_today", **FULL_WIDTH):
            st.session_state["diary_ref_date"] = date.today()
        if nav_cols[2].button("Next", key="sp_diary_next", **FULL_WIDTH):
            if diary_view_mode == "Week":
                st.session_state["diary_ref_date"] += timedelta(days=7)
            else:
                st.session_state["diary_ref_date"] = add_months(st.session_state["diary_ref_date"], 1)

        diary_ref_date = st.session_state["diary_ref_date"]

        if diary_view_mode == "Week":
            week_start = diary_ref_date - timedelta(days=diary_ref_date.weekday())
            week_days = [week_start + timedelta(days=i) for i in range(7)]
            st.caption(f"Week of {week_start.strftime('%d %b %Y')}")

            day_cols = st.columns(7)
            for col, day in zip(day_cols, week_days):
                with col:
                    is_today = day == date.today()
                    st.markdown(f"{'🔵 ' if is_today else ''}**{day.strftime('%a %d %b')}**")
                    day_appts = appointments_by_date.get(day.isoformat(), [])
                    if not day_appts:
                        st.caption("—")
                    else:
                        for appt in day_appts:
                            render_diary_appointment(appt)
        else:
            st.caption(diary_ref_date.strftime("%B %Y"))
            weeks = calendar.monthcalendar(diary_ref_date.year, diary_ref_date.month)

            header_cols = st.columns(7)
            for col, day_name in zip(header_cols, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
                col.markdown(f"**{day_name}**")

            for week_idx, week in enumerate(weeks):
                week_cols = st.columns(7)
                for col_idx, (col, day_num) in enumerate(zip(week_cols, week)):
                    with col:
                        # Keyed per cell position (not day number) — the blank
                        # filler cells all have day_num 0 and would collide.
                        with st.container(key=f"day-{diary_ref_date.year}-{diary_ref_date.month}-{week_idx}-{col_idx}"):
                            if day_num == 0:
                                st.markdown("&nbsp;")
                                continue
                            day_date = date(diary_ref_date.year, diary_ref_date.month, day_num)
                            is_today = day_date == date.today()
                            st.markdown(f"{'🔵 ' if is_today else ''}**{day_num}**")
                            day_appts = appointments_by_date.get(day_date.isoformat(), [])
                            if day_appts:
                                with st.popover(f"{len(day_appts)} 📅", **FULL_WIDTH):
                                    for appt in day_appts:
                                        render_diary_appointment(appt)

    # --- 4. Consultant Performance ---
    with st.container(key="card-sp-perf"):
        section_header(
            4, "Consultant Performance",
            f"Deals by consultant across the whole timeframe ({timeframe_option}), ignoring the consultant and stage filters.",
        )
        if not time_filtered_df.empty:
            rep_summary = (
                time_filtered_df.groupby("Sales Rep")
                .agg(
                    Total_Deals=("Client Name", "count"),
                    Deals_Won=("Status", lambda x: int(stage_in(x, STAGES_WON).sum())),
                    Deals_In_Progress=("Status", lambda x: int(stage_in(x, STAGES_ACTIVE).sum())),
                    Deals_Booked=("Status", lambda x: int(stage_in(x, STAGES_EARLY).sum())),
                    Deals_Lost=("Status", lambda x: int(stage_in(x, STAGES_LOST).sum())),
                )
                .reset_index()
                .sort_values(["Deals_Won", "Total_Deals"], ascending=False)
            )
            rep_summary.columns = ["Sales Rep", "Total Deals", "Won", "In Progress", "Booked", "Lost"]
            st.dataframe(rep_summary, **DF_WIDTH, hide_index=True)

            won_by_rep = rep_summary.set_index("Sales Rep")["Won"]
            won_by_rep = won_by_rep[won_by_rep > 0].sort_values(ascending=False)
            sales_report["rep_summary"] = rep_summary
            sales_report["won_by_rep"] = won_by_rep
            if not won_by_rep.empty:
                sales_report["top_rep"] = (won_by_rep.index[0], int(won_by_rep.iloc[0]))
            if not won_by_rep.empty:
                st.caption("Leaderboard — deals won per consultant")
                render_leaderboard(won_by_rep, "Consultant", "Deals won")
        else:
            st.info("Insufficient data for consultant metrics in this timeframe.")

    # --- 5. Stage Breakdown ---
    with st.container(key="card-sp-stages"):
        section_header(5, "Stage Breakdown", f"How many deals sit at each stage ({timeframe_option}).")
        if not time_filtered_df.empty:
            tracked_stages = STAGES_EARLY + STAGES_ACTIVE + ["Sold", "Closed Won", "Closed Lost", "Not Sold"]
            lowered = time_filtered_df["Status"].astype(str).str.lower()
            stage_counts = [
                {"Stage / Status": stage, "Total Count": int((lowered == stage.lower()).sum())}
                for stage in tracked_stages
            ]
            # Any stage in the data that isn't one of the standard ones above
            # (e.g. a new stage added in Zoho, or "Lost") would otherwise be
            # silently left out of the breakdown — list them too.
            known = {s.lower() for s in tracked_stages}
            other_stages = sorted({s for s in time_filtered_df["Status"].astype(str) if s and s.lower() not in known})
            for stage in other_stages:
                stage_counts.append(
                    {"Stage / Status": f"{stage} (other)", "Total Count": int((time_filtered_df["Status"] == stage).sum())}
                )
            sales_report["stages"] = [
                {**row, "color": STAGE_DOT_COLORS.get(row["Stage / Status"].replace(" (other)", "").lower(), "#7C83FF")}
                for row in stage_counts
            ]
            st.dataframe(pd.DataFrame(stage_counts), **DF_WIDTH, hide_index=True)
        else:
            st.info("No data available for stage breakdown.")

    # --- 6. Sold Deals (Closed Won) ---
    with st.container(key="card-sp-sold"):
        section_header(
            6, "Sold Deals (Closed Won)",
            "Deals closed won in the chosen period, with the lease value sold per consultant.",
        )
        sold_syc_only = st.toggle(
            "SYComms-owned deals only",
            value=False,
            key="sold_syc_only",
            help="Off = every Closed Won deal in Zoho (SYComms and SYPLUS). On = only deals owned by a @sycomms.co.uk consultant.",
        )

        if deals_error:
            st.info("Sold deals are unavailable while the deals feed is down (see the error above).")
        else:
            sold_deals_df = sold_source_df[sold_source_df["Status"] == CLOSED_WON_STAGE].copy()
            if sold_syc_only:
                sold_deals_df = sold_deals_df[sold_deals_df["Owner Email"].str.endswith(SYCOMMS_EMAIL_DOMAIN.lower())]

            if sold_deals_df.empty:
                st.info("No Closed Won deals found.")
            else:
                sold_deals_df["Closing Date"] = sold_deals_df["Closing Date"].apply(parse_zoho_date)

                sold_range_start_ts, sold_range_end_ts = render_date_range_picker(
                    "Show deals closed between",
                    key="sold_deals_date_range",
                    default_window_days=SOLD_DEALS_WINDOW_DAYS,
                    reference_date=today.date(),
                )

                st.caption(
                    f"Closed Won from {sold_range_start_ts.strftime('%d/%m/%Y')} to "
                    f"{sold_range_end_ts.strftime('%d/%m/%Y')}."
                )

                recent_deals_df = sold_deals_df[
                    sold_deals_df["Closing Date"].between(sold_range_start_ts, sold_range_end_ts)
                ].sort_values("Closing Date", ascending=False)

                if recent_deals_df.empty:
                    st.info("No deals closed won in the selected date range.")
                else:
                    deals_display_df = recent_deals_df[
                        [
                            "Client Name", "Account Name", "Sales Rep", "Monthly Lease Spend",
                            "Total Lease Value", "Monthly Network Spend", "Closing Date", "Deal ID",
                        ]
                    ].rename(columns={"Client Name": "Deal Name", "Sales Rep": "Sales Consultant"}).copy()
                    deals_display_df["Closing Date"] = deals_display_df["Closing Date"].dt.strftime("%d/%m/%Y")
                    deals_display_df["Open in Zoho"] = deals_display_df["Deal ID"].apply(zoho_deal_url)
                    deals_display_df = deals_display_df.drop(columns=["Deal ID"])
                    for col in ["Monthly Lease Spend", "Total Lease Value", "Monthly Network Spend"]:
                        deals_display_df[col] = deals_display_df[col].apply(money)

                    st.dataframe(
                        deals_display_df,
                        hide_index=True,
                        **DF_WIDTH,
                        column_config={"Open in Zoho": st.column_config.LinkColumn(display_text="Open ↗")},
                    )
                    report["sold"] = {
                        "df": recent_deals_df, "range": (sold_range_start_ts, sold_range_end_ts),
                        "total": float(recent_deals_df["Total Lease Value"].sum()), "syc_only": sold_syc_only,
                    }
                    st.metric("Total sold this period", money(recent_deals_df["Total Lease Value"].sum()))

                    st.caption("Leaderboard — value sold per consultant")
                    consultant_totals = (
                        recent_deals_df.assign(
                            **{"Sales Rep": recent_deals_df["Sales Rep"].replace("", "Unassigned")}
                        )
                        .groupby("Sales Rep")["Total Lease Value"]
                        .sum()
                        .sort_values(ascending=False)
                    )
                    render_leaderboard(consultant_totals, "Consultant", "Total Lease Value sold (£)")


# =====================================================================
# TAB 3 — ASSESSMENT
# One person at a time: deals they created in Zoho (credited by "Created By")
# next to their outbound phone activity from the Grandstream UCM CDR export.
# =====================================================================
CONVERSATION_SECONDS = 30  # a connected call at least this long counts as a real conversation
ASM_TIMEFRAMES = ["Week", "Month", "Quarter", "Year"]
ASM_CDR_KEEP = [
    "CDR", "Caller Number", "Caller Name", "Callee Number", "Start Time", "Talk Time",
    "Call Status", "Call Type", "Unique ID", "Session",
]
ASM_CDR_NEED = ["CDR", "Caller Number", "Callee Number", "Start Time", "Call Status", "Call Type"]
asm_pdf_slot = None  # the assessment PDF button is placed here, once the PDF code further down has been defined


# ---- call records (Grandstream UCM CDR) ----
def _cdr_decode(raw):
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw[:3] == b"\xef\xbb\xbf":
        return raw[3:].decode("utf-8")
    if raw[:200].count(b"\x00") > 40:
        return raw.decode("utf-16-le")
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def _cdr_expand(blobs):
    """Unpacks .tar / .zip / .gz uploads (the UCM's bulk download is a tar of monthly CSVs)."""
    import gzip
    import tarfile
    import zipfile

    out = []
    for b in blobs:
        if b[:2] == b"\x1f\x8b":
            try:
                out.extend(_cdr_expand([gzip.decompress(b)]))
                continue
            except OSError:
                pass
        if b[:4] == b"PK\x03\x04":
            with zipfile.ZipFile(io.BytesIO(b)) as z:
                inner = [z.read(n) for n in sorted(z.namelist()) if not n.endswith("/") and "__MACOSX" not in n]
            out.extend(_cdr_expand(inner))
            continue
        if len(b) > 262 and b[257:262] == b"ustar":
            with tarfile.open(fileobj=io.BytesIO(b)) as t:
                inner = [t.extractfile(m).read() for m in sorted(t.getmembers(), key=lambda m: m.name) if m.isfile()]
            out.extend(_cdr_expand(inner))
            continue
        out.append(b)
    return out


def parse_cdr_outbound(blobs):
    """Grandstream UCM CDR export(s) -> one row per OUTBOUND call.

    The UCM writes a `main_cdr` row per call plus `sub_cdr` rows for each leg, so only `main_cdr` rows are read.
    A call is 'connected' when the UCM says ANSWERED and there was some talk time (a call answered with zero talk
    is the other end hanging up as it was picked up). Overlapping exports (e.g. a monthly file plus the current
    month's file) are de-duplicated."""
    frames = []
    for b in _cdr_expand(blobs):
        try:
            t = pd.read_csv(
                io.StringIO(_cdr_decode(b)), dtype=str, keep_default_na=False,
                usecols=lambda c: c.strip() in ASM_CDR_KEEP,
            )
        except (pd.errors.EmptyDataError, ValueError):
            continue
        t.columns = [c.strip() for c in t.columns]
        missing = [c for c in ASM_CDR_NEED if c not in t.columns]
        if missing:
            raise ValueError(
                "That doesn't look like a Grandstream UCM CDR export - missing column(s): " + ", ".join(missing)
            )
        frames.append(t)
    if not frames:
        raise ValueError("No call records were found in the file(s) you uploaded.")
    t = pd.concat(frames, ignore_index=True)
    for c in ("Caller Name", "Talk Time", "Unique ID", "Session"):
        if c not in t.columns:
            t[c] = ""
    t = t[(t["CDR"].str.strip() == "main_cdr") & (t["Call Type"].str.strip().str.lower() == "outbound")].copy()
    t = t.drop_duplicates(subset=["Session", "Unique ID", "Start Time", "Caller Number"])
    out = pd.DataFrame(
        {
            "ts": pd.to_datetime(t["Start Time"].str.strip(), errors="coerce"),
            "ext": t["Caller Number"].str.strip(),
            "name": t["Caller Name"].str.strip(),
            "dialled": t["Callee Number"].str.strip(),
            "status": t["Call Status"].str.strip().str.upper(),
            "talk_s": pd.to_numeric(t["Talk Time"], errors="coerce").fillna(0).astype(int),
        }
    ).dropna(subset=["ts"])
    out["name"] = out["name"].where(out["name"] != "", "Ext " + out["ext"])
    out["connected"] = (out["status"] == "ANSWERED") & (out["talk_s"] > 0)
    return out.sort_values("ts").reset_index(drop=True)


def _norm_name(v):
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", str(v).lower()).split())


def suggest_identities(person, identities):
    """Which phone identities (extension + name on the CDR) look like this person?

    Extensions get handed on from one person to the next, so the name stamped on each call record is the safer
    thing to match on. Returns (list of (ext, name), how it matched)."""
    pn = _norm_name(person)
    ptoks = pn.split()
    if not ptoks:
        return [], "none"
    exact = [k for k in identities if _norm_name(k[1]) == pn]
    if exact:
        return exact, "exact"
    first = [
        k for k in identities
        if _norm_name(k[1]).split()
        and _norm_name(k[1]).split()[0] == ptoks[0]
        and set(_norm_name(k[1]).split()) <= set(ptoks)
    ]
    return (first, "first name only") if first else ([], "none")


# ---- Zoho users ----
@st.cache_data(ttl=3600)
def get_zoho_users():
    """Active Zoho users as [{'name', 'email'}], or ([], reason) when the token can't read the Users API."""
    try:
        token = get_access_token()
        headers = {"Authorization": f"Zoho-oauthtoken {token}"}
        users, page = [], 1
        while True:
            resp = requests.get(
                f"{ZOHO_API_DOMAIN}/crm/v2/users", headers=headers,
                params={"type": "ActiveUsers", "per_page": 200, "page": page}, timeout=20,
            )
            if resp.status_code != 200:
                return [], f"status {resp.status_code}"
            payload = resp.json()
            users.extend(payload.get("users", []))
            if not payload.get("info", {}).get("more_records"):
                break
            page += 1
        return [
            {"name": (u.get("full_name") or "").strip(), "email": (u.get("email") or "").lower()}
            for u in users if (u.get("full_name") or "").strip()
        ], None
    except Exception as err:  # never let a nice-to-have lookup break the tab
        return [], str(err)


# ---- Zoho leads (the telemarketers' own leads, identified by Lead Source) ----
# A big org can have tens of thousands of leads, so nothing here downloads them all: the picker's choices come
# from the Lead Source field's own list of options (one quick call), and leads are then fetched with Zoho's search
# - only for the chosen source(s), and only back to the start of the comparison period.
LEAD_COLUMNS = ["Lead ID", "Name", "Company", "Source", "Status", "Created Time", "Created By", "Converted"]


@st.cache_data(ttl=3600)
def get_lead_source_options():
    """Lead Source choices as defined on the Leads module (falls back to the sources on the newest leads)."""
    token = get_access_token()
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    names = []
    try:
        resp = requests.get(
            f"{ZOHO_API_DOMAIN}/crm/v2/settings/fields", headers=headers, params={"module": "Leads"}, timeout=20
        )
        if resp.status_code == 200:
            for fld in resp.json().get("fields", []):
                if fld.get("api_name") == "Lead_Source":
                    names = [
                        (v.get("display_value") or v.get("actual_value") or "").strip()
                        for v in fld.get("pick_list_values", [])
                    ]
    except Exception:
        names = []
    names = [n for n in names if n and n != "-None-"]
    if not names:  # no access to field settings: use the sources found on the newest leads instead
        resp = requests.get(
            f"{ZOHO_API_DOMAIN}/crm/v2/Leads", headers=headers, timeout=30,
            params={"fields": "Lead_Source", "sort_by": "Created_Time", "sort_order": "desc", "per_page": 200},
        )
        if resp.status_code == 200:
            names = sorted({(r.get("Lead_Source") or "").strip() for r in resp.json().get("data", [])} - {""})
        elif resp.status_code != 204:
            raise RuntimeError(f"Zoho CRM API returned an error fetching Leads (status {resp.status_code}): {resp.text}")
    return sorted(dict.fromkeys(names), key=str.lower)


LEAD_FIELD_LIST = "Last_Name,First_Name,Company,Lead_Source,Lead_Status,Created_Time,Created_By,Converted__s"


def _enrich_leads(records, headers):
    """Zoho's search can return a slimmed-down record with no Created Time / Status. For those, fetch the
    fields we need by id (100 per call). Returns (records with the extras merged in, what happened)."""
    missing = [r["id"] for r in records if r.get("id") and "Created_Time" not in r]
    info = {"needed": len(missing), "fetched": 0, "error": ""}
    if not missing:
        return records, info
    by_id = {}
    for i in range(0, len(missing), 100):
        chunk = ",".join(missing[i:i + 100])
        for extra in ({"converted": "both"}, {}):
            try:
                resp = requests.get(
                    f"{ZOHO_API_DOMAIN}/crm/v2/Leads", headers=headers, timeout=30,
                    params={"ids": chunk, "fields": LEAD_FIELD_LIST, **extra},
                )
            except Exception as err:
                info["error"] = f"could not reach Zoho: {err}"
                break
            if resp.status_code == 200:
                for rec in resp.json().get("data", []):
                    by_id[rec.get("id")] = rec
                break
            info["error"] = f"status {resp.status_code}: {resp.text[:300]}"
    info["fetched"] = len(by_id)
    return [{**r, **by_id.get(r.get("id"), {})} for r in records], info


@st.cache_data(ttl=300)
def probe_lead_dates(sample_id):
    """Troubleshooting: ask Zoho three different ways where a lead's created date lives. Returns plain-text lines."""
    token = get_access_token()
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    lines = []

    def call(path, params=None):
        try:
            resp = requests.get(f"{ZOHO_API_DOMAIN}/crm/v2/{path}", headers=headers, params=params or {}, timeout=30)
            return resp.status_code, (resp.json() if resp.status_code == 200 else resp.text[:300])
        except Exception as err:
            return 0, str(err)

    code, body = call("settings/fields", {"module": "Leads"})
    if code == 200:
        found = [
            f"{f.get('api_name')} ({f.get('field_label')}, {f.get('data_type')})"
            for f in body.get("fields", [])
            if re.search(r"creat|time|date", f"{f.get('api_name')} {f.get('field_label')}", re.I)
        ]
        lines.append("Date/time fields on your Leads module: " + (", ".join(found) or "none found"))
    else:
        lines.append(f"Couldn't read the Leads field list (status {code}: {body})")

    if sample_id:
        code, body = call(f"Leads/{sample_id}")
        if code == 200 and body.get("data"):
            rec = body["data"][0]
            shown = {k: rec[k] for k in rec if re.search(r"creat|time|date|modif", k, re.I)}
            lines.append(f"One whole lead record from Zoho - its date/time fields: {shown or 'none present'}")
        else:
            lines.append(f"Fetching a single lead failed (status {code}: {body})")

    code, body = call("Leads", {"fields": "Created_Time,Created_By,Lead_Source", "sort_by": "Created_Time",
                                "sort_order": "desc", "per_page": 3})
    if code == 200:
        lines.append(f"Three newest leads in the whole Leads module: {body.get('data')}")
    else:
        lines.append(f"Listing the newest leads failed (status {code}: {body})")
    return lines


def _crit_escape(value):
    """Zoho search criteria treat ( ) , and backslash as special - escape them in a value."""
    return re.sub(r"([\\(),])", r"\\\1", value)


def _search_leads_for_source(source, since_iso, headers):
    """All leads with this exact Lead Source created on/after `since_iso`, converted ones included.
    Returns (records, how) where `how` says which kind of request finally worked.

    Steps down through simpler requests if this Zoho org rejects part of one, and - because a date filter that
    Zoho quietly misreads looks exactly like 'no leads' - if the date-narrowed search finds nothing it looks again
    across all dates (the dates are then checked here instead)."""
    src = f"(Lead_Source:equals:{_crit_escape(source)})"
    timed = f"({src}and(Created_Time:greater_equal:{since_iso}))"
    variants = [
        ("date-narrowed, converted included", {"criteria": timed, "converted": "both"}, True),
        ("date-narrowed", {"criteria": timed}, True),
        ("all dates, converted included", {"criteria": src, "converted": "both"}, False),
        ("all dates", {"criteria": src}, False),
    ]
    last, timed_came_back_empty = None, False
    for how, params, is_timed in variants:
        if is_timed and timed_came_back_empty:
            continue
        records, ok = [], False
        for with_fields in (True, False):
            extra = {"fields": LEAD_FIELD_LIST} if with_fields else {}
            records, page, ok = [], 1, True
            while True:
                try:
                    resp = requests.get(
                        f"{ZOHO_API_DOMAIN}/crm/v2/Leads/search", headers=headers,
                        params={**params, **extra, "per_page": 200, "page": page}, timeout=30,
                    )
                except Exception as err:
                    raise RuntimeError(f"Could not reach Zoho CRM API for Leads. Details: {err}")
                if resp.status_code == 204:
                    break
                if resp.status_code != 200:
                    last, ok = f"status {resp.status_code}: {resp.text}", False
                    break
                payload = resp.json()
                records.extend(payload.get("data", []))
                if not payload.get("info", {}).get("more_records") or page >= 10:  # Zoho search caps at 2,000 records
                    break
                page += 1
            if ok:
                break
        if not ok:
            continue
        if records:
            return records, how
        if is_timed:
            timed_came_back_empty = True  # maybe really none - or the date filter was misread: look at all dates too
            continue
        return records, how + " (nothing found)"
    if timed_came_back_empty:
        return [], "date-narrowed (nothing found)"
    raise RuntimeError(f"Zoho CRM API returned an error searching Leads ({last})")


@st.cache_data(ttl=300)
def load_leads_for_sources(sources, since_iso):
    """Leads for the chosen sources since `since_iso`. Returns (DataFrame, converted_known, how-they-were-found)."""
    token = get_access_token()
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    records, diag = [], []
    for source in sources:
        found, how = _search_leads_for_source(source, since_iso, headers)
        raw_keys = sorted(found[0].keys()) if found else []
        found, enrich = _enrich_leads(found, headers)
        records.extend(found)
        stamps = [parse_appt(r.get("Created_Time")) for r in found]
        stamps = [t for t in stamps if pd.notna(t)]
        diag.append(
            {
                "source": source, "how": how, "returned": len(found), "dated": len(stamps),
                "raw_keys": raw_keys, "enrich": enrich, "sample_id": (found[0].get("id") if found else None),
                "newest": max(stamps) if stamps else None, "oldest": min(stamps) if stamps else None,
            }
        )
    converted_known = any("Converted__s" in r or "$converted" in r for r in records)
    rows = []
    for r in records:
        flag = r.get("Converted__s", r.get("$converted"))
        rows.append(
            {
                "Lead ID": r.get("id"),
                "Name": " ".join(x for x in [r.get("First_Name"), r.get("Last_Name")] if x),
                "Company": r.get("Company") or "",
                "Source": (r.get("Lead_Source") or "").strip(),
                "Status": r.get("Lead_Status") or "",
                "Created Time": parse_appt(r.get("Created_Time")),
                "Created By": (r.get("Created_By") or {}).get("name") or "",
                "Converted": bool(flag) if flag is not None else False,
            }
        )
    df = pd.DataFrame(rows, columns=LEAD_COLUMNS).drop_duplicates(subset=["Lead ID"])
    df["Created Time"] = pd.to_datetime(df["Created Time"], errors="coerce")
    df["Converted"] = df["Converted"].astype(bool)
    return df, converted_known, diag


# ---- time frames ----
def period_bounds(kind, ref):
    if kind == "Week":
        start = ref - timedelta(days=ref.weekday())
        return start, start + timedelta(days=6)
    if kind == "Month":
        start = ref.replace(day=1)
        return start, add_months(start, 1) - timedelta(days=1)
    if kind == "Quarter":
        start = date(ref.year, 3 * ((ref.month - 1) // 3) + 1, 1)
        return start, add_months(start, 3) - timedelta(days=1)
    return date(ref.year, 1, 1), date(ref.year, 12, 31)


def shift_period(kind, ref, n):
    if kind == "Week":
        return ref + timedelta(days=7 * n)
    if kind == "Month":
        return add_months(ref, n)
    if kind == "Quarter":
        return add_months(ref, 3 * n)
    return add_months(ref, 12 * n)


def period_label(kind, start, end):
    if kind == "Week":
        return f"Week of {start.strftime('%d %b')} - {end.strftime('%d %b %Y')}"
    if kind == "Month":
        return start.strftime("%B %Y")
    if kind == "Quarter":
        return f"Q{(start.month - 1) // 3 + 1} {start.year}"
    return str(start.year)


def _between(series, start, end):
    """Inclusive date window on a datetime Series (NaT is never inside)."""
    return (series >= pd.Timestamp(start)) & (series < pd.Timestamp(end) + pd.Timedelta(days=1))


def fmt_talk(seconds):
    seconds = int(round(seconds or 0))
    if seconds >= 3600:
        return f"{seconds // 3600}h {seconds % 3600 // 60:02d}m"
    if seconds >= 60:
        return f"{seconds // 60}m {seconds % 60:02d}s"
    return f"{seconds}s"


def md_bold(text, wrap):
    """Turns **bold** markers into whatever bold the output needs; `wrap` also escapes each piece."""
    parts = text.split("**")
    return "".join(wrap(p, i % 2 == 1) for i, p in enumerate(parts))


def delta_sub(cur, prev, fmt=None, unit="", lower_is_better=False):
    """('+4 vs 3 previous', tone) for a tile's small print."""
    fmt = fmt or (lambda v: f"{v:,.0f}")
    diff = cur - prev
    if diff == 0:
        return f"same as previous ({fmt(prev)}{unit})", ""
    good = (diff > 0) != lower_is_better
    sign = "+" if diff > 0 else "-"
    return f"{sign}{fmt(abs(diff))}{unit} vs {fmt(prev)}{unit} previous", ("good" if good else "bad")


def _bin_spec(kind):
    return {"Week": "D", "Month": "D", "Quarter": "W", "Year": "M"}[kind]


def bin_counts(ts, start, end, kind, mask=None):
    """Counts per day / week / month across the period, zero-filled. Returns a list of (label, count)."""
    freq = _bin_spec(kind)
    periods = pd.period_range(start, end, freq=freq)
    if mask is not None:
        ts = ts[mask]
    counts = ts.dt.to_period(freq).value_counts() if len(ts) else pd.Series(dtype=int)
    out = []
    for p in periods:
        if freq == "D":
            label = p.start_time.strftime("%a %d") if kind == "Week" else p.start_time.strftime("%d")
        elif freq == "W":
            label = max(p.start_time.date(), start).strftime("%d %b")
        else:
            label = p.start_time.strftime("%b")
        out.append((label, int(counts.get(p, 0))))
    return out


def render_bins_chart(rows, height=190):
    """rows: [(label, series_name, count)] in display order. Dark, non-interactive stacked columns."""
    chart_df = pd.DataFrame(rows, columns=["Bin", "Series", "Count"])
    chart_df["Order"] = chart_df.groupby("Series").cumcount()
    names = list(dict.fromkeys(chart_df["Series"]))
    palette = {"Deals created": "#7C83FF", "Connected": "#34D399", "Not connected": "#5E6A82"}
    spare = ["#7C83FF", "#38D6F5", "#34D399", "#FBBF24", "#FB923C", "#F472B6", "#A78BFA"]
    chart = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("Bin:N", sort=alt.EncodingSortField("Order"), title="", axis=alt.Axis(labelAngle=0, labelOverlap=True)),
            y=alt.Y("Count:Q", title="", axis=alt.Axis(tickMinStep=1)),
            color=alt.Color(
                "Series:N",
                scale=alt.Scale(domain=names, range=[palette.get(n, spare[i % len(spare)]) for i, n in enumerate(names)]),
                legend=alt.Legend(orient="top", title=None, labelColor="#8C98B0") if len(names) > 1 else None,
            ),
            tooltip=["Bin", "Series", "Count"],
        )
        .properties(height=height)
        .configure(background="transparent")
        .configure_axis(labelColor="#8C98B0", titleColor="#8C98B0", gridColor="#1C2740", domainColor="#26324D", tickColor="#26324D")
        .configure_view(strokeOpacity=0)
    )
    try:
        st.altair_chart(chart, width="stretch", theme=None)
    except TypeError:
        st.altair_chart(chart, use_container_width=True, theme=None)


def render_assessment():
    global asm_pdf_slot
    today_d = now_uk.date()
    st.session_state.setdefault("asm_ref", today_d)

    # ------------------------------------------------------------------ 1. who and when
    with st.container(key="card-asm-pick"):
        section_header(1, "Assessment", "Pick a person and a time frame - deals created in Zoho next to their phone activity.")
        if deals_error:
            st.error(f"🚨 Could not load deals from Zoho, so there is nothing to assess yet: {deals_error}")
            return

        zoho_users, users_error = get_zoho_users()
        created_names = sorted({n for n in deals_df["Created By"] if n})
        by_key = {}
        for name in [u["name"] for u in zoho_users] + created_names:
            by_key.setdefault(_norm_name(name), name)
        people = sorted(by_key.values(), key=str.lower)

        pc1, pc2 = st.columns([2, 1])
        person = pc1.selectbox(
            "Person", people, index=None, placeholder="Search for a person...", key="asm_person",
            help="Everyone in Zoho. Type to search.",
        )
        tf = pc2.selectbox("Time frame", ASM_TIMEFRAMES, index=1, key="asm_tf")
        if users_error and not zoho_users:
            st.caption(
                "Showing everyone who has created a deal, because the Zoho connection can't read the full user "
                f"list yet ({users_error}). Adding the ZohoCRM.users.READ scope to the token fixes that."
            )

        ref = st.session_state["asm_ref"]
        s0, e0 = period_bounds(tf, ref)
        nav = st.columns([1, 1, 1, 4])
        if nav[0].button("Previous", key="asm_prev", **FULL_WIDTH):
            st.session_state["asm_ref"] = shift_period(tf, ref, -1)
        if nav[1].button(f"This {tf.lower()}", key="asm_now", **FULL_WIDTH):
            st.session_state["asm_ref"] = today_d
        if nav[2].button("Next", key="asm_next", disabled=e0 >= today_d, **FULL_WIDTH):
            st.session_state["asm_ref"] = shift_period(tf, ref, 1)
        start, end = period_bounds(tf, st.session_state["asm_ref"])
        in_progress = start <= today_d <= end
        label = period_label(tf, start, end)

        # previous window for comparison: the same number of elapsed days when this period is still running
        pstart, pend = period_bounds(tf, shift_period(tf, start, -1))
        if in_progress:
            pend = min(pend, pstart + timedelta(days=(today_d - start).days))
            compare_label = f"the same point last {tf.lower()}"
        else:
            compare_label = f"the previous {tf.lower()}"
        render_html(
            chip(label, "accent") + " " + chip(("In progress - compared with " if in_progress else "Compared with ") + compare_label)
        )

    # ------------------------------------------------------------------ 2. call data
    with st.container(key="card-asm-cdr"):
        section_header(
            2, "Call data",
            "Upload the Grandstream UCM CDR export(s) - monthly CSVs, or the .tar / .zip / .gz bulk download as it comes.",
        )
        files = st.file_uploader(
            "Grandstream CDR file(s)", accept_multiple_files=True, key="asm_cdr_files",
            help="Nothing is stored - the files only live in this browser session.",
        )
        sig = tuple(sorted((f.name, f.size) for f in files)) if files else None
        if sig != st.session_state.get("asm_cdr_sig"):
            st.session_state["asm_cdr_sig"] = sig
            st.session_state["asm_cdr"], st.session_state["asm_cdr_err"] = None, None
            if files:
                try:
                    with st.spinner("Reading call records..."):
                        st.session_state["asm_cdr"] = parse_cdr_outbound([f.getvalue() for f in files])
                except Exception as err:
                    st.session_state["asm_cdr_err"] = str(err)
        cdr = st.session_state.get("asm_cdr")
        if st.session_state.get("asm_cdr_err"):
            st.error(f"Couldn't read that file: {st.session_state['asm_cdr_err']}")

        identities, chosen = [], []
        if cdr is not None:
            counts = cdr.groupby(["ext", "name"]).size().sort_values(ascending=False)
            identities = list(counts.index)
            ident_key = lambda k: f"{k[0]}|{k[1]}"
            if cdr.empty:
                st.warning("The file(s) loaded fine but contain no outbound calls.")
            else:
                render_html(
                    chip(f"{len(cdr):,} outbound calls", "accent")
                    + " "
                    + chip(f"{cdr['ts'].min().strftime('%d %b %Y')} to {cdr['ts'].max().strftime('%d %b %Y')}")
                    + " "
                    + chip(f"{len(identities)} phone names / extensions")
                )
            if person:
                suggested, how = suggest_identities(person, identities)
                labels = {ident_key(k): f"{k[1]} (ext {k[0]}) - {int(counts[k]):,} calls" for k in identities}
                suggested_keys = [ident_key(k) for k in suggested]
                ms_key = f"asm_ids_{abs(hash(sig)) % 10**8}_{_norm_name(person)}"
                chosen = st.multiselect(
                    f"Phone identities to count as {person}",
                    options=list(labels), default=suggested_keys, format_func=lambda k: labels[k], key=ms_key,
                    help="Extensions get passed from person to person, so each is listed with the name on the call "
                         "record. Tick every one that belongs to this person.",
                )
                if how == "first name only" and chosen == suggested_keys:
                    st.caption("Matched on first name only - check this really is the right person before relying on the call numbers.")
                elif how == "none" and not chosen:
                    st.caption(f"No call-record name matches {person} - pick their extension(s) from the list above.")
        elif not st.session_state.get("asm_cdr_err"):
            st.caption("No call data loaded yet - add the CDR to include phone activity in the assessment.")

    # ------------------------------------------------------------------ results
    if not person:
        with st.container(key="card-asm-empty"):
            render_html(
                '<div class="pe-empty"><div class="ico"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" '
                'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div>'
                '<div><div class="t">Choose someone to assess</div><ol>'
                "<li>Search for the person in the picker above</li>"
                "<li>Choose Week, Month, Quarter or Year (and step back through earlier periods)</li>"
                "<li>Upload the CDR export to add their phone activity</li></ol></div></div>"
            )
        return

    # ------------------------------------------------------------------ 3. lead sources (optional)
    lead_sel, leads_df, leads_err, conv_known, lead_diag = [], None, None, False, []
    with st.container(key="card-asm-leadpick"):
        section_header(
            3, "Lead sources (optional)",
            "For telemarketers who add their own leads in Zoho - pick the lead source(s) to measure, or leave blank to skip.",
        )
        try:
            source_options = get_lead_source_options()
        except Exception as err:
            source_options, leads_err = [], str(err)
        if not leads_err:
            first_tok = (_norm_name(person).split() or [""])[0]
            hinted = [x for x in source_options if first_tok and _norm_name(x).startswith(first_tok[:3])]
            lead_sel = st.multiselect(
                f"Lead sources to measure for {person}",
                options=sorted(source_options, key=lambda x: (x not in hinted, x.lower())),
                key=f"asm_leadsrc_{_norm_name(person)}", placeholder="Leave blank to skip leads",
                help="The Lead Source choices set up in Zoho. Pick several to add them together.",
            )
            if hinted and not lead_sel:
                st.caption("Possible matches for this name: " + ", ".join(hinted[:6]))
            if not source_options:
                st.caption("No lead sources were found in Zoho.")
            if lead_sel:
                try:
                    with st.spinner("Fetching leads from Zoho..."):
                        leads_df, conv_known, lead_diag = load_leads_for_sources(
                            tuple(sorted(lead_sel)), (datetime.combine(pstart, datetime.min.time()) - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00+00:00"),
                        )
                except Exception as err:
                    leads_err, lead_sel = str(err), []
        if leads_err:
            st.warning(
                "Couldn't read the Leads from Zoho, so lead numbers are skipped for now. If this says the token "
                f"isn't allowed, it needs the ZohoCRM.modules.leads.READ scope. Details: {leads_err}"
            )

    pkey = _norm_name(person)
    mine = deals_df[deals_df["Created By"].map(_norm_name) == pkey]

    def deal_stats(a, b):
        created = mine[_between(mine["Created Time"], a, b)]
        closing = pd.to_datetime(mine["Closing Date"], errors="coerce")
        won_all = stage_in(mine["Status"], STAGES_WON) if len(mine) else pd.Series(dtype=bool)
        won_period = mine[won_all & _between(closing, a, b)] if len(mine) else mine
        cohort_won = created[stage_in(created["Status"], STAGES_WON)] if len(created) else created
        return created, won_period, cohort_won

    created, won_period, cohort_won = deal_stats(start, end)
    p_created, p_won_period, p_cohort_won = deal_stats(pstart, pend)

    def call_stats(a, b):
        if cdr is None or not chosen:
            return None
        c = cdr[(cdr["ext"] + "|" + cdr["name"]).isin(chosen)]
        c = c[_between(c["ts"], a, b)]
        conn = c[c["connected"]]
        return {
            "df": c, "made": len(c), "connected": len(conn),
            "conversations": int((conn["talk_s"] >= CONVERSATION_SECONDS).sum()),
            "talk": int(conn["talk_s"].sum()),
        }

    calls = call_stats(start, end)
    p_calls = call_stats(pstart, pend)

    n_created, n_won, n_cohort = len(created), len(won_period), len(cohort_won)
    won_value = float(won_period["Total Lease Value"].sum())
    p_won_value = float(p_won_period["Total Lease Value"].sum())
    cohort_pct = (n_cohort / n_created * 100) if n_created else 0.0

    deal_tiles, call_tiles = [], []
    sub, tone = delta_sub(n_created, len(p_created))
    deal_tiles.append(("Deals created", n_created, "", sub, tone))
    sub, tone = delta_sub(n_won, len(p_won_period))
    deal_tiles.append(("Closed won in period", n_won, "good", sub, tone))
    deal_tiles.append((
        "This period's deals now won", f"{n_cohort} of {n_created}" if n_created else "-", "cyan",
        f"{cohort_pct:.0f}% conversion" if n_created else "no deals created", "",
    ))
    sub, tone = delta_sub(won_value, p_won_value, fmt=money_short)
    deal_tiles.append(("Won lease value", money_short(won_value), "good", sub, tone))

    if calls is None:
        why = "Upload the CDR" if cdr is None else "Pick a phone identity"
        for lab, t_ in (("Calls made", ""), ("Connected", "good"), (f"Conversations {CONVERSATION_SECONDS}s+", "cyan"), ("Talk time", "warn")):
            call_tiles.append((lab, "-", t_, why, ""))
    else:
        pc = p_calls
        sub, tone = delta_sub(calls["made"], pc["made"])
        call_tiles.append(("Calls made", f"{calls['made']:,}", "", sub, tone))
        rate = calls["connected"] / calls["made"] * 100 if calls["made"] else 0.0
        p_rate = pc["connected"] / pc["made"] * 100 if pc["made"] else 0.0
        diff_pts = round(rate) - round(p_rate)
        sub = (f"same rate as previous ({p_rate:.0f}%)" if diff_pts == 0
               else f"{'+' if diff_pts > 0 else '-'}{abs(diff_pts)} pts vs {p_rate:.0f}% previous")
        tone = "" if diff_pts == 0 else ("good" if diff_pts > 0 else "bad")
        call_tiles.append(("Connected", f"{calls['connected']:,} · {rate:.0f}%", "good", sub, tone))
        sub, tone = delta_sub(calls["conversations"], pc["conversations"])
        call_tiles.append((f"Conversations {CONVERSATION_SECONDS}s+", f"{calls['conversations']:,}", "cyan", sub, tone))
        sub, tone = delta_sub(calls["talk"], pc["talk"], fmt=fmt_talk)
        call_tiles.append(("Talk time", fmt_talk(calls["talk"]), "warn", sub, tone))

    # ---- leads
    def lead_stats(a, b):
        if not lead_sel or leads_df is None:
            return None
        l = leads_df[leads_df["Source"].isin(lead_sel) & _between(leads_df["Created Time"], a, b)]
        return {"df": l, "added": len(l), "converted": int(l["Converted"].sum()) if conv_known else None}

    leads_now, leads_prev = lead_stats(start, end), lead_stats(pstart, pend)
    lead_tiles = None
    if leads_now is not None:
        lead_tiles = []
        sub, tone = delta_sub(leads_now["added"], leads_prev["added"])
        lead_tiles.append(("Leads added", f"{leads_now['added']:,}", "", sub, tone))
        if conv_known:
            sub, tone = delta_sub(leads_now["converted"], leads_prev["converted"])
            lead_tiles.append(("Converted", f"{leads_now['converted']:,}", "good", sub, tone))
            rate_l = leads_now["converted"] / leads_now["added"] * 100 if leads_now["added"] else 0.0
            p_rate_l = leads_prev["converted"] / leads_prev["added"] * 100 if leads_prev["added"] else 0.0
            dpl = round(rate_l) - round(p_rate_l)
            lead_tiles.append((
                "Conversion rate", f"{rate_l:.0f}%", "cyan",
                f"same as previous ({p_rate_l:.0f}%)" if dpl == 0 else f"{'+' if dpl > 0 else '-'}{abs(dpl)} pts vs {p_rate_l:.0f}% previous",
                "" if dpl == 0 else ("good" if dpl > 0 else "bad"),
            ))
        else:
            lead_tiles.append(("Converted", "n/a", "good", "Zoho didn't return conversion data", ""))
            lead_tiles.append(("Conversion rate", "n/a", "cyan", "", ""))
        by_src = leads_now["df"]["Source"].value_counts()
        lead_tiles.append((
            "Busiest source", by_src.index[0] if len(by_src) else "-", "warn",
            f"{int(by_src.iloc[0])} lead(s)" if len(by_src) else "no leads in period", "",
        ))

    # ---- highlights
    points = []
    if n_created:
        by_owner = created["Sales Rep"].replace("", "Unassigned").value_counts()
        points.append(
            f"**{person}** created **{n_created}** deal(s) in {label} (previous: {len(p_created)}), "
            f"mostly for **{by_owner.index[0]}** ({int(by_owner.iloc[0])})."
        )
    else:
        points.append(f"**{person}** created **no deals** in {label} (previous: {len(p_created)}).")
    if n_created or n_won:
        points.append(
            f"**{n_won}** of their deals closed won in the period, worth **{money(won_value)}** in lease value; "
            f"**{n_cohort}** of the **{n_created}** created this period have already been won."
        )
    if calls is not None:
        if calls["made"]:
            avg = calls["talk"] / calls["connected"] if calls["connected"] else 0
            days_active = calls["df"]["ts"].dt.date.nunique()
            points.append(
                f"**{calls['made']:,}** outbound call(s) over **{days_active}** active day(s), **{calls['connected']:,}** connected "
                f"({calls['connected'] / calls['made'] * 100:.0f}%); **{fmt_talk(calls['talk'])}** talk time, "
                f"averaging **{fmt_talk(avg)}** per connected call."
            )
            if n_created and calls["connected"]:
                points.append(f"That is roughly **{calls['connected'] / n_created:.1f}** connected calls per deal created.")
        else:
            points.append(
                "**No outbound calls** were found for the selected phone identity in this period - check the "
                "identities ticked above, and that the CDR covers these dates."
            )
        if cdr is not None and len(cdr) and (cdr["ts"].min().date() > start or (cdr["ts"].max().date() < min(end, today_d))):
            points.append(
                f"Heads up: the CDR only covers **{cdr['ts'].min().strftime('%d %b %Y')} to {cdr['ts'].max().strftime('%d %b %Y')}**, "
                "so call numbers for this period may be understated."
            )

    if leads_now is not None:
        names_txt = ", ".join(lead_sel)
        txt = (f"**{leads_now['added']:,}** lead(s) added from **{names_txt}** in {label} "
               f"(previous: {leads_prev['added']:,})")
        if conv_known and leads_now["added"]:
            txt += f", **{leads_now['converted']}** converted ({leads_now['converted'] / leads_now['added'] * 100:.0f}%)"
        points.append(txt + ".")
        by_status = leads_now["df"]["Status"].replace("", "(no status)").value_counts()
        if len(by_status):
            points.append("Lead status: " + ", ".join(f"**{k}** {int(v)}" for k, v in by_status.head(6).items()) + ".")

    # ------------------------------------------------------------------ scorecard
    with st.container(key="card-asm-score"):
        section_header(4, f"{person} - scorecard", f"{label}  ·  deals credited by Created By in Zoho")
        render_html('<div class="pe-subhead"><span class="n">Deals</span></div>')
        for col, (lab, val, t_, sub_, st_) in zip(st.columns(4), deal_tiles):
            with col:
                render_html(kpi_tile(lab, val, tone=t_, sub=sub_, sub_tone=st_))
        render_html('<div class="pe-subhead"><span class="n">Phone calls (outbound)</span></div>')
        for col, (lab, val, t_, sub_, st_) in zip(st.columns(4), call_tiles):
            with col:
                render_html(kpi_tile(lab, val, tone=t_, sub=sub_, sub_tone=st_))
        if lead_tiles is not None:
            render_html(f'<div class="pe-subhead"><span class="n">Leads they added ({esc(", ".join(lead_sel))})</span></div>')
            for col, (lab, val, t_, sub_, st_) in zip(st.columns(4), lead_tiles):
                with col:
                    render_html(kpi_tile(lab, val, tone=t_, sub=sub_, sub_tone=st_))
        st.caption(
            f"Connected = answered with some talk time. A conversation is a connected call of {CONVERSATION_SECONDS} seconds or more."
        )
        render_html(
            '<div class="pe-callout">'
            + "<br>".join("• " + md_bold(p, lambda t, b: f"<b>{esc(t)}</b>" if b else esc(t)) for p in points)
            + "</div>"
        )
        render_html('<div style="height:10px"></div>')
        asm_pdf_slot = st.empty()

    # ------------------------------------------------------------------ 4. activity
    deal_bins = bin_counts(created["Created Time"], start, end, tf)
    call_conn_bins = call_other_bins = None
    if calls is not None:
        call_conn_bins = bin_counts(calls["df"]["ts"], start, end, tf, mask=calls["df"]["connected"])
        all_bins = bin_counts(calls["df"]["ts"], start, end, tf)
        call_other_bins = [(lab, a - c) for (lab, a), (_, c) in zip(all_bins, call_conn_bins)]
    with st.container(key="card-asm-activity"):
        gran_word = {"D": "Per day", "W": "Per week", "M": "Per month"}[_bin_spec(tf)]
        section_header(5, "Activity over time", f"{gran_word} across {label}.")
        ac1, ac2 = st.columns(2)
        with ac1:
            st.caption("Deals created")
            render_bins_chart([(lab, "Deals created", n) for lab, n in deal_bins])
        with ac2:
            st.caption("Outbound calls")
            if call_conn_bins is None:
                st.caption("Add the CDR and pick a phone identity to see calls here.")
            else:
                render_bins_chart(
                    [(lab, "Connected", n) for lab, n in call_conn_bins]
                    + [(lab, "Not connected", n) for lab, n in call_other_bins]
                )

    # ------------------------------------------------------------------ 5. deals
    created_sorted = created.sort_values("Created Time", ascending=False)
    with st.container(key="card-asm-deals"):
        section_header(6, "Deals", f"Created by {person} in {label}, and the ones that closed won.")
        dc1, dc2 = st.columns(2)
        with dc1:
            st.caption("Booked for (deal owner)")
            by_owner = created["Sales Rep"].replace("", "Unassigned").value_counts()
            if by_owner.empty:
                st.caption("No deals created in this period.")
            else:
                render_leaderboard(by_owner, "Sales consultant", "Deals created")
        with dc2:
            st.caption("Where this period's deals stand now")
            stage_df = created["Status"].replace("", "(no stage)").value_counts().rename_axis("Stage").reset_index(name="Deals")
            if stage_df.empty:
                st.caption("No deals created in this period.")
            else:
                st.dataframe(stage_df, hide_index=True, **DF_WIDTH)

        st.caption(f"Deals created ({n_created})")
        created_rows = []
        if created_sorted.empty:
            st.caption("None in this period.")
        else:
            view = created_sorted[["Created Time", "Client Name", "Account Name", "Sales Rep", "Status", "Parsed Date", "Deal ID"]].copy()
            view["Created Time"] = view["Created Time"].dt.strftime("%d/%m/%Y %H:%M")
            view["Appointment"] = view["Parsed Date"].apply(lambda d: d.strftime("%d/%m/%Y %H:%M") if pd.notna(d) else "-")
            view["Open in Zoho"] = view["Deal ID"].apply(zoho_deal_url)
            view = view.drop(columns=["Parsed Date", "Deal ID"]).rename(
                columns={"Created Time": "Created", "Client Name": "Deal", "Sales Rep": "Booked for", "Status": "Stage"}
            )
            created_rows = view.drop(columns=["Open in Zoho"]).values.tolist()
            st.dataframe(view, hide_index=True, **DF_WIDTH,
                         column_config={"Open in Zoho": st.column_config.LinkColumn(display_text="Open ↗")})

        st.caption(f"Closed won in period ({n_won})")
        won_rows = []
        if won_period.empty:
            st.caption("None in this period.")
        else:
            wv = won_period.copy()
            wv["Closing"] = pd.to_datetime(wv["Closing Date"], errors="coerce")
            wv = wv.sort_values("Closing", ascending=False)
            won_rows = [
                [r["Client Name"], r["Sales Rep"] or "Unassigned", fmt_date_uk(r["Closing"]),
                 money(r["Monthly Network Spend"]), money(r["Total Lease Value"])]
                for _, r in wv.iterrows()
            ]
            wview = pd.DataFrame(won_rows, columns=["Deal", "Booked for", "Closed", "Monthly network", "Lease value"])
            wview["Open in Zoho"] = wv["Deal ID"].apply(zoho_deal_url).values
            st.dataframe(wview, hide_index=True, **DF_WIDTH,
                         column_config={"Open in Zoho": st.column_config.LinkColumn(display_text="Open ↗")})

    lead_bins_total, lead_src_rows, lead_status_rows = None, [], []
    if leads_now is not None:
        ldf = leads_now["df"]
        lead_bins_total = bin_counts(ldf["Created Time"], start, end, tf)
        lead_src_rows = [(src, int((ldf["Source"] == src).sum())) for src in lead_sel]
        lead_status_rows = [(str(k), int(v)) for k, v in ldf["Status"].replace("", "(no status)").value_counts().items()]
        with st.container(key="card-asm-leads"):
            section_header(7, "Leads", f"Leads from {', '.join(lead_sel)}, added in {label}.")
            lc1, lc2 = st.columns(2)
            with lc1:
                st.caption("Leads added")
                if ldf.empty:
                    st.caption("No leads from these sources in this period.")
                else:
                    chart_rows = []
                    for src in lead_sel[:6]:
                        chart_rows += [(lab, src, n) for lab, n in bin_counts(ldf["Created Time"], start, end, tf, mask=(ldf["Source"] == src))]
                    if len(lead_sel) > 6:
                        rest = ldf["Source"].isin(lead_sel[6:])
                        chart_rows += [(lab, "Other sources", n) for lab, n in bin_counts(ldf["Created Time"], start, end, tf, mask=rest)]
                    render_bins_chart(chart_rows)
            with lc2:
                st.caption("By lead source")
                src_table = pd.DataFrame({"Lead source": lead_sel, "Leads": [n for _, n in lead_src_rows]})
                if conv_known:
                    conv_by = ldf.groupby("Source")["Converted"].sum().reindex(lead_sel).fillna(0).astype(int).values
                    src_table["Converted"] = conv_by
                st.dataframe(src_table, hide_index=True, **DF_WIDTH)
                st.caption("By lead status (as set on each lead in Zoho)")
                if lead_status_rows:
                    st.dataframe(pd.DataFrame(lead_status_rows, columns=["Status", "Leads"]), hide_index=True, **DF_WIDTH)
                else:
                    st.caption("No leads in this period.")

    if leads_now is not None and lead_diag:
        with st.expander("How these leads were found"):
            for dgn in lead_diag:
                span = (f", created between {dgn['oldest']:%d %b %Y} and {dgn['newest']:%d %b %Y}"
                        if dgn["newest"] is not None else "")
                st.write(f"**{dgn['source']}** - Zoho returned {dgn['returned']:,} lead(s){span} ({dgn['how']}).")
                if dgn["returned"] and dgn["dated"] < dgn["returned"]:
                    en = dgn["enrich"]
                    st.caption(
                        f"Fields in Zoho's search result: {', '.join(dgn['raw_keys']) or '(none)'}.  "
                        f"Looked up the rest by id: {en['fetched']:,} of {en['needed']:,}"
                        + (f" - Zoho said: {en['error']}" if en["error"] else "") + "."
                    )
                    st.warning(
                        f"Only {dgn['dated']:,} of those {dgn['returned']:,} came back with a Created Time, so the rest "
                        "can't be placed in a time frame."
                    )
            if any(d["returned"] and d["dated"] < d["returned"] for d in lead_diag):
                st.caption("Technical details for troubleshooting:")
                try:
                    probe_id = next((d["sample_id"] for d in lead_diag if d["sample_id"]), None)
                    for line in probe_lead_dates(probe_id):
                        st.code(line, language=None)
                except Exception as err:
                    st.caption(f"Couldn't run the troubleshooting lookups: {err}")
            st.caption(
                f"Only leads whose Created Time falls in {label} are counted above "
                f"({leads_now['added']:,} of the {sum(d['returned'] for d in lead_diag):,} returned)."
            )

    stage_rows = [
        (str(r["Stage"]), int(r["Deals"]), STAGE_DOT_COLORS.get(str(r["Stage"]).lower(), "#7C83FF"))
        for _, r in (created["Status"].replace("", "(no stage)").value_counts().rename_axis("Stage").reset_index(name="Deals").iterrows())
    ]
    report["assessment"] = {
        "person": person, "tf": tf, "label": label, "compare": compare_label,
        "deal_tiles": deal_tiles, "call_tiles": call_tiles, "points": points,
        "deal_bins": deal_bins,
        "call_bins": None if call_conn_bins is None else [
            (lab, a + b, c) for (lab, a), (_, b), (_, c) in zip(call_conn_bins, call_other_bins, call_conn_bins)
        ],
        "booked_for": [(k, int(v)) for k, v in created["Sales Rep"].replace("", "Unassigned").value_counts().items()],
        "stage_rows": stage_rows, "created_rows": created_rows, "won_rows": won_rows,
        "n_created": n_created, "n_won": n_won, "won_value": won_value,
        "lead_tiles": lead_tiles, "lead_names": ", ".join(lead_sel), "lead_bins": lead_bins_total,
        "lead_sources": lead_src_rows, "lead_status": lead_status_rows,
    }


def money_short(v):
    return f"£{v:,.0f}" if abs(v) >= 1000 else f"£{v:,.2f}"


def fmt_date_uk(v):
    return v.strftime("%d/%m/%Y") if pd.notna(v) else "-"


with tab_assess:
    render_assessment()


# =====================================================================
# PDF BRIEFING — a 2-3 page dark-themed summary of both tabs, built from
# whatever is currently on screen (filters, date ranges and all).
# Needs the `reportlab` package; if it isn't installed the rest of the app
# carries on and the sidebar simply explains what to add.
# =====================================================================
try:
    import io

    from reportlab.lib import colors as rl_colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        BaseDocTemplate, CondPageBreak, Flowable, Frame, PageBreak, PageTemplate,
        Paragraph, Spacer, Table, TableStyle,
    )
    from reportlab.pdfbase.pdfmetrics import stringWidth

    REPORTLAB_OK = True
except ImportError:  # pragma: no cover - depends on the deployment
    REPORTLAB_OK = False

_PDF = {
    "bg": "#0A0E1A", "surface": "#111827", "surface2": "#161F33", "surface3": "#1C2740",
    "border": "#273049", "text": "#E7EAF3", "muted": "#8C98B0", "faint": "#5E6A82",
    "accent": "#7C83FF", "cyan": "#38D6F5", "good": "#34D399", "warn": "#FBBF24", "bad": "#F87171",
}
_TONE = {"": "accent", "bad": "bad", "warn": "warn", "good": "good", "muted": "faint", "cyan": "cyan"}


def _hx(key):
    return rl_colors.HexColor(_PDF.get(key, key))


def _mix(fg, bg, alpha):
    """Blend colour `fg` over `bg` — how the app's translucent tints look on dark."""
    f, b = _hx(fg), _hx(bg)
    return rl_colors.Color(
        f.red * alpha + b.red * (1 - alpha),
        f.green * alpha + b.green * (1 - alpha),
        f.blue * alpha + b.blue * (1 - alpha),
    )


def _clean(v):
    """Plain text that the PDF's built-in font can print (anything it can't becomes '?')."""
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    return str(v).encode("cp1252", "replace").decode("cp1252")


def _t(v):
    """_clean + escaped for use inside a Paragraph."""
    return _clean(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fit(text, font, size, max_w):
    text = _clean(text)
    if stringWidth(text, font, size) <= max_w:
        return text
    while text and stringWidth(text + "...", font, size) > max_w:
        text = text[:-1]
    return text.rstrip() + "..."


if REPORTLAB_OK:

    class _Header(Flowable):
        def __init__(self, width, generated):
            super().__init__()
            self.width, self.height, self.generated = width, 22 * mm, generated

        def wrap(self, aw, ah):
            return self.width, self.height

        def draw(self):
            c, h = self.canv, self.height
            c.setFillColor(_hx("accent"))
            c.roundRect(0, h - 13 * mm, 13 * mm, 13 * mm, 3.2 * mm, fill=1, stroke=0)
            c.setFillColor(_hx("bg"))
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(6.5 * mm, h - 8.6 * mm, "SC")
            x = 17.5 * mm
            c.setFillColor(_hx("good"))
            c.circle(x + 1 * mm, h - 2.2 * mm, 0.9 * mm, fill=1, stroke=0)
            c.setFillColor(_hx("cyan"))
            c.setFont("Helvetica-Bold", 6.8)
            c.drawString(x + 3.2 * mm, h - 3.1 * mm, "MANAGEMENT BRIEFING  -  LIVE FROM ZOHO CRM")
            c.setFillColor(_hx("text"))
            c.setFont("Helvetica-Bold", 19)
            first = "SYComms Renewals & Sales "
            c.drawString(x, h - 11 * mm, first)
            c.setFillColor(_hx("cyan"))
            c.drawString(x + stringWidth(first, "Helvetica-Bold", 19), h - 11 * mm, "Command Center")
            c.setFillColor(_hx("muted"))
            c.setFont("Helvetica", 8)
            c.drawString(x, h - 16.2 * mm, self.generated)
            c.setStrokeColor(_hx("border"))
            c.setLineWidth(0.6)
            c.line(0, 0.5 * mm, self.width, 0.5 * mm)

    class _Section(Flowable):
        def __init__(self, width, num, title, subtitle=""):
            super().__init__()
            self.width, self.height = width, 11 * mm
            self.num, self.title, self.subtitle = num, title, subtitle

        def wrap(self, aw, ah):
            return self.width, self.height

        def draw(self):
            c, h = self.canv, self.height
            c.setFillColor(_mix("accent", "bg", 0.16))
            c.setStrokeColor(_mix("accent", "bg", 0.35))
            c.setLineWidth(0.6)
            c.roundRect(0, 1.5 * mm, 8.5 * mm, 8.5 * mm, 2.2 * mm, fill=1, stroke=1)
            c.setFillColor(_hx("accent"))
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(4.25 * mm, 4.2 * mm, str(self.num))
            c.setFillColor(_hx("text"))
            c.setFont("Helvetica-Bold", 12)
            c.drawString(11.5 * mm, 6.4 * mm, _clean(self.title))
            c.setFillColor(_hx("muted"))
            c.setFont("Helvetica", 7.3)
            c.drawString(11.5 * mm, 2.3 * mm, _fit(self.subtitle, "Helvetica", 7.3, self.width - 12 * mm))

    class _KpiRow(Flowable):
        """Tiles of (label, value, tone) or (label, value, tone, small print, small-print tone)."""

        def __init__(self, width, items):
            super().__init__()
            self.width, self.items = width, items
            self.has_sub = any(len(i) > 3 and i[3] for i in items)
            self.height = (21 if self.has_sub else 17) * mm

        def wrap(self, aw, ah):
            return self.width, self.height

        def draw(self):
            c, h = self.canv, self.height
            gap = 3 * mm
            n = len(self.items)
            w = (self.width - gap * (n - 1)) / n
            for i, item in enumerate(self.items):
                label, value, tone = item[0], item[1], item[2]
                sub = item[3] if len(item) > 3 else ""
                sub_tone = item[4] if len(item) > 4 else ""
                x = i * (w + gap)
                c.setFillColor(_hx("surface"))
                c.setStrokeColor(_hx("border"))
                c.setLineWidth(0.6)
                c.roundRect(x, 0, w, h, 2.6 * mm, fill=1, stroke=1)
                c.setStrokeColor(_hx(_TONE.get(tone, "accent")))
                c.setLineWidth(1.6)
                c.line(x + 3 * mm, h - 0.5 * mm, x + w - 3 * mm, h - 0.5 * mm)
                c.setFillColor(_hx("muted"))
                lab, lsize = str(label).upper(), 5.9
                while lsize > 4.6 and stringWidth(lab, "Helvetica-Bold", lsize) > w - 5 * mm:
                    lsize -= 0.2
                c.setFont("Helvetica-Bold", lsize)
                c.drawString(x + 2.5 * mm, h - 5.6 * mm, _fit(lab, "Helvetica-Bold", lsize, w - 5 * mm))
                value = _clean(value)
                size = 17
                while size > 8 and stringWidth(value, "Helvetica-Bold", size) > w - 5 * mm:
                    size -= 1
                c.setFillColor(_hx("text"))
                c.setFont("Helvetica-Bold", size)
                c.drawString(x + 2.5 * mm, (8.4 if sub else 3.6) * mm, value)
                if sub:
                    c.setFillColor(_hx({"good": "good", "bad": "bad"}.get(sub_tone, "muted")))
                    c.setFont("Helvetica", 5.9)
                    c.drawString(x + 2.5 * mm, 2.9 * mm, _fit(sub, "Helvetica", 5.9, w - 5 * mm))

    class _BarList(Flowable):
        """Horizontal bars: label on the left, value on the right."""

        def __init__(self, width, rows, color="accent", label_w=36 * mm, fmt=None):
            super().__init__()
            self.width, self.rows, self.color, self.label_w = width, rows, color, label_w
            self.fmt = fmt or (lambda v: f"{v:g}")
            self.rh = 6 * mm
            self.height = max(len(rows), 1) * self.rh

        def wrap(self, aw, ah):
            return self.width, self.height

        def draw(self):
            c = self.canv
            vmax = max([v for _, v, *_ in self.rows] + [1e-9])
            val_w = 17 * mm
            track_x, track_w = self.label_w, self.width - self.label_w - val_w
            for i, row in enumerate(self.rows):
                label, value = row[0], row[1]
                colour = row[2] if len(row) > 2 else self.color
                y = self.height - (i + 1) * self.rh
                c.setFillColor(_hx("text"))
                c.setFont("Helvetica", 7.4)
                c.drawString(0, y + 2.1 * mm, _fit(label, "Helvetica", 7.4, self.label_w - 2 * mm))
                c.setFillColor(_hx("surface3"))
                c.roundRect(track_x, y + 1.7 * mm, track_w, 2.8 * mm, 1.2 * mm, fill=1, stroke=0)
                bw = track_w * (value / vmax) if vmax > 0 else 0
                if value > 0:
                    c.setFillColor(_hx(colour))
                    c.roundRect(track_x, y + 1.7 * mm, max(bw, 2 * mm), 2.8 * mm, 1.2 * mm, fill=1, stroke=0)
                c.setFillColor(_hx("text"))
                c.setFont("Helvetica-Bold", 7.4)
                c.drawRightString(self.width, y + 2.1 * mm, self.fmt(value))

    class _ColumnChart(Flowable):
        """Columns of (label, value, colour, sub-label) or (..., inner) where `inner` is drawn over the base of the column."""

        def __init__(self, width, cols, height=36 * mm, label_every=1, show_values=True):
            super().__init__()
            self.width, self.height, self.cols = width, height, cols
            self.label_every, self.show_values = label_every, show_values

        def wrap(self, aw, ah):
            return self.width, self.height

        def draw(self):
            c = self.canv
            n = len(self.cols)
            pitch = self.width / n
            base, top = 8 * mm, self.height - 5 * mm
            vmax = max([col[1] for col in self.cols] + [1])
            c.setStrokeColor(_hx("border"))
            c.setLineWidth(0.6)
            c.line(0, base, self.width, base)
            for i, col in enumerate(self.cols):
                label, value, colour, sub = col[0], col[1], col[2], col[3]
                inner = col[4] if len(col) > 4 else None
                x = i * pitch
                bh = (top - base) * (value / vmax)
                if value > 0:
                    c.setFillColor(_hx(colour))
                    c.roundRect(x + pitch * 0.18, base, pitch * 0.64, max(bh, 1.2 * mm), 0.9 * mm, fill=1, stroke=0)
                    if inner:
                        c.setFillColor(_hx("good"))
                        ih = (top - base) * (inner / vmax)
                        c.roundRect(x + pitch * 0.18, base, pitch * 0.64, max(ih, 1.0 * mm), 0.9 * mm, fill=1, stroke=0)
                    if self.show_values:
                        c.setFillColor(_hx("text"))
                        c.setFont("Helvetica-Bold", 6.6)
                        c.drawCentredString(x + pitch / 2, base + max(bh, 1.2 * mm) + 1 * mm, str(int(value)))
                if i % self.label_every == 0:
                    c.setFillColor(_hx("muted"))
                    c.setFont("Helvetica", 5.6)
                    c.drawCentredString(x + pitch / 2, base - 3.2 * mm, label)
                    if sub:
                        c.setFillColor(_hx("faint"))
                        c.setFont("Helvetica", 5.2)
                        c.drawCentredString(x + pitch / 2, base - 6 * mm, sub)

    def _styles():
        mk = ParagraphStyle
        return {
            "th": mk("th", fontName="Helvetica-Bold", fontSize=6.2, leading=7.6, textColor=_hx("muted")),
            "thr": mk("thr", fontName="Helvetica-Bold", fontSize=6.2, leading=7.6, textColor=_hx("muted"), alignment=2),
            "td": mk("td", fontName="Helvetica", fontSize=7.3, leading=9, textColor=_hx("text")),
            "tdr": mk("tdr", fontName="Helvetica", fontSize=7.3, leading=9, textColor=_hx("text"), alignment=2),
            "note": mk("note", fontName="Helvetica", fontSize=6.8, leading=8.5, textColor=_hx("muted")),
            "hl": mk("hl", fontName="Helvetica", fontSize=8, leading=11.6, textColor=_hx("text")),
            "lbl": mk("lbl", fontName="Helvetica-Bold", fontSize=6.6, leading=8, textColor=_hx("muted")),
        }

    def _cell(value, right, st):
        if isinstance(value, dict):  # {"t": text, "color": key, "bold": True}
            text = _t(value.get("t"))
            if value.get("bold"):
                text = f"<b>{text}</b>"
            if value.get("color"):
                text = f'<font color="{_PDF.get(value["color"], value["color"])}">{text}</font>'
            return Paragraph(text, st["tdr"] if right else st["td"])
        return Paragraph(_t(value), st["tdr"] if right else st["td"])

    def _table(st, header, rows, widths, right=(), row_tints=None):
        data = [[Paragraph(_t(h).upper(), st["thr"] if i in right else st["th"]) for i, h in enumerate(header)]]
        for r in rows:
            data.append([_cell(v, i in right, st) for i, v in enumerate(r)])
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), _hx("surface3")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_hx("surface"), _hx("surface2")]),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, _hx("border")),
            ("BOX", (0, 0), (-1, -1), 0.6, _hx("border")),
            ("ROUNDEDCORNERS", [3, 3, 3, 3]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]
        for i, tint in (row_tints or {}).items():
            style.append(("BACKGROUND", (0, i + 1), (-1, i + 1), tint))
        t = Table(data, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle(style))
        return t

    def _callout(st, width, lines):
        body = "<br/>".join(f'<font color="{_PDF["accent"]}">&#8226;</font>&nbsp; {ln}' for ln in lines)
        t = Table([[Paragraph(body, st["hl"])]], colWidths=[width])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _hx("surface2")),
            ("BOX", (0, 0), (-1, -1), 0.6, _hx("border")),
            ("LINEBEFORE", (0, 0), (0, -1), 2.4, _hx("accent")),
            ("ROUNDEDCORNERS", [3, 3, 3, 3]),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return t

    def _bold(v):
        return f'<b><font color="{_PDF["text"]}">{_t(v)}</font></b>'

    def _pair(left, right, width):
        gap = 6 * mm
        half = (width - gap) / 2
        t = Table([[left, "", right]], colWidths=[half, gap, half])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        return t, half

    def _fmt_date(v):
        return v.strftime("%d/%m/%Y") if pd.notna(v) else "-"

    def _assessment_story(A, st, W, num):
        """The assessment page(s): used on its own and as the last page of the full briefing."""
        story = [_Section(W, num, f"Assessment - {A['person']}", f"{A['label']}  -  compared with {A['compare']}"),
                 Spacer(1, 1.5 * mm), Paragraph("DEALS  -  credited by Created By in Zoho", st["lbl"]), Spacer(1, 1.5 * mm),
                 _KpiRow(W, A["deal_tiles"]), Spacer(1, 3.5 * mm),
                 Paragraph("PHONE CALLS  -  outbound, from the Grandstream UCM call records", st["lbl"]), Spacer(1, 1.5 * mm),
                 _KpiRow(W, A["call_tiles"]), Spacer(1, 3.5 * mm)]
        if A.get("lead_tiles"):
            story += [Paragraph(f"LEADS THEY ADDED  -  lead source(s): {_t(A['lead_names'])}", st["lbl"]), Spacer(1, 1.5 * mm),
                      _KpiRow(W, A["lead_tiles"]), Spacer(1, 3.5 * mm)]
        story.append(_callout(st, W, [md_bold(p, lambda t, b: _bold(t) if b else _t(t)) for p in A["points"]]))
        story.append(Spacer(1, 4 * mm))

        half = (W - 6 * mm) / 2
        def chart(cols, colour):
            n = len(cols)
            return _ColumnChart(half, [(lab, v, colour, "", *extra) for lab, v, *extra in cols], height=28 * mm,
                                label_every=max(1, -(-n // 12)), show_values=n <= 16)
        left = [Paragraph(f"DEALS CREATED  -  {_t(A['tf']).lower()}", st["lbl"]), Spacer(1, 1.5 * mm),
                chart(A["deal_bins"], "accent") if any(v for _, v in A["deal_bins"])
                else Paragraph("No deals were created in this period.", st["note"])]
        if A["call_bins"] is None or not any(v for _, v, _c in A["call_bins"]):
            right = [Paragraph("OUTBOUND CALLS", st["lbl"]), Spacer(1, 1.5 * mm),
                     Paragraph("No call data was loaded for this assessment." if A["call_bins"] is None
                               else "No outbound calls found for this person in the period.", st["note"])]
        else:
            right = [Paragraph("OUTBOUND CALLS  -  total, with connected in green", st["lbl"]), Spacer(1, 1.5 * mm),
                     chart(A["call_bins"], "faint")]
        pair, _ = _pair(left, right, W)
        story += [pair, Spacer(1, 4 * mm)]

        if A.get("lead_bins") is not None:
            hl = (W - 6 * mm) / 2
            nb = len(A["lead_bins"])
            lchart = (_ColumnChart(hl, [(lab, v, "cyan", "") for lab, v in A["lead_bins"]], height=28 * mm,
                                   label_every=max(1, -(-nb // 12)), show_values=nb <= 16)
                      if any(v for _, v in A["lead_bins"]) else Paragraph("No leads from these sources in this period.", st["note"]))
            ll = [Paragraph(f"LEADS ADDED  -  {_t(A['tf']).lower()}", st["lbl"]), Spacer(1, 1.5 * mm), lchart]
            lr = [Paragraph("BY LEAD SOURCE", st["lbl"]), Spacer(1, 1.5 * mm),
                  _BarList(hl, [(k, v) for k, v in A["lead_sources"][:5]], color="cyan", label_w=32 * mm, fmt=lambda v: f"{int(v)}")]
            if A["lead_status"]:
                lr += [Spacer(1, 2 * mm), Paragraph("BY LEAD STATUS", st["lbl"]), Spacer(1, 1.5 * mm),
                       _BarList(hl, [(k, v) for k, v in A["lead_status"][:4]], color="accent", label_w=32 * mm, fmt=lambda v: f"{int(v)}")]
            pairl, _ = _pair(ll, lr, W)
            story += [pairl, Spacer(1, 4 * mm)]

        if A["booked_for"]:
            hh = (W - 6 * mm) / 2
            lb = [Paragraph("BOOKED FOR (DEAL OWNER)", st["lbl"]), Spacer(1, 1.5 * mm),
                  _BarList(hh, [(k, v) for k, v in A["booked_for"][:6]], color="accent", label_w=32 * mm, fmt=lambda v: f"{int(v)}")]
            rb = [Paragraph("WHERE THIS PERIOD'S DEALS STAND", st["lbl"]), Spacer(1, 1.5 * mm),
                  _BarList(hh, [(k, v, c) for k, v, c in A["stage_rows"][:6]], color="accent", label_w=34 * mm, fmt=lambda v: f"{int(v)}")]
            pair2, _ = _pair(lb, rb, W)
            story += [pair2, Spacer(1, 4 * mm)]

        if A["created_rows"]:
            story.append(CondPageBreak(50 * mm))
            story += [Paragraph(f"DEALS CREATED  -  {A['n_created']} in the period", st["lbl"]), Spacer(1, 1.5 * mm)]
            rows = [[r[0], {"t": r[1], "bold": True}, r[2], r[3], r[4], r[5]] for r in A["created_rows"][:6]]
            story.append(_table(st, ["Created", "Deal", "Account", "Booked for", "Stage", "Appointment"], rows,
                                [26 * mm, 40 * mm, 34 * mm, 30 * mm, 24 * mm, 28 * mm]))
            if len(A["created_rows"]) > 6:
                story += [Spacer(1, 1 * mm), Paragraph(f"Showing the latest 6 of {len(A['created_rows'])} - the full list is in the app.", st["note"])]
            story.append(Spacer(1, 3 * mm))
        if A["won_rows"]:
            story.append(CondPageBreak(40 * mm))
            story += [Paragraph(f"CLOSED WON IN THE PERIOD  -  {A['n_won']} deal(s), {_t(money_short(A['won_value']))} lease value", st["lbl"]),
                      Spacer(1, 1.5 * mm)]
            rows = [[{"t": r[0], "bold": True}, r[1], r[2], r[3], r[4]] for r in A["won_rows"][:5]]
            story.append(_table(st, ["Deal", "Booked for", "Closed", "Monthly network", "Lease value"], rows,
                                [62 * mm, 40 * mm, 24 * mm, 28 * mm, 28 * mm], right=(3, 4)))
            if len(A["won_rows"]) > 5:
                story += [Spacer(1, 1 * mm), Paragraph(f"Showing the latest 5 of {len(A['won_rows'])} - the full list is in the app.", st["note"])]
        return story

    def _render_pdf(story, title):
        W = A4[0] - 28 * mm

        def _page(canv, doc):
            canv.saveState()
            canv.setFillColor(_hx("bg"))
            canv.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
            canv.setFillColor(_hx("faint"))
            canv.setFont("Helvetica", 6.6)
            canv.drawString(14 * mm, 7 * mm, "SYComms  -  Renewals & Sales Command Center")
            canv.drawRightString(A4[0] - 14 * mm, 7 * mm, f"Page {doc.page}")
            canv.restoreState()

        buf = io.BytesIO()
        doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=12 * mm,
                              bottomMargin=14 * mm, title=title, author="SYComms")
        doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(14 * mm, 14 * mm, W, A4[1] - 26 * mm, id="f",
                                                                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
                                           onPage=_page)])
        doc.build(story)
        return buf.getvalue()

    def build_assessment_pdf(R):
        """One-person assessment on its own, from the `report['assessment']` data."""
        W = A4[0] - 28 * mm
        story = [_Header(W, f"Assessment generated {R['generated']}"), Spacer(1, 4 * mm)]
        story += _assessment_story(R["assessment"], _styles(), W, 1)
        return _render_pdf(story, f"Assessment - {R['assessment']['person']}")

    def build_pdf_report(R):
        """Builds the PDF from the `R` dict the app fills in as it renders, returns bytes."""
        st = _styles()
        W = A4[0] - 28 * mm
        gbp = lambda v: f"£{v:,.0f}" if abs(v) >= 1000 else f"£{v:,.2f}"
        story = [_Header(W, f"Generated {R['generated']}  -  follows the filters and date ranges selected in the app"), Spacer(1, 4 * mm)]

        # ---------------- 1. Renewals ----------------
        df, today_ts = R["df"], R["today"]
        story.append(_Section(W, 1, "Renewals", f"{len(df)} SYC Customer accounts tracked  -  {R['ren_filters']}"))
        story.append(Spacer(1, 1.5 * mm))
        story.append(_KpiRow(W, [(l, v, tone) for l, v, _a, tone in R["ren_tiles"]]))
        story.append(Spacer(1, 3.5 * mm))

        live = df[~df["Rolling Contract"]]
        reds = live[live["Urgency"] == "Red"].sort_values("Days Remaining")
        overdue = int((live["Days Remaining"] < 0).sum())
        points = []
        if len(reds):
            first = reds.iloc[0]
            points.append(
                f"{_bold(len(reds))} account(s) are Red (under 12 months left). Soonest: {_bold(first['Account Name'])} "
                f"- {_t(first['Time Remaining'])} (ends {_fmt_date(first['Contract End Date'])})."
            )
        else:
            points.append(f"{_bold(0)} accounts are Red - nothing is due to expire within 12 months.")
        if overdue:
            points.append(f"{_bold(overdue)} of those are already past their contract end date - chase these first.")
        points.append(
            f"{_bold(int((df['Urgency'] == 'Amber').sum()))} account(s) are Amber (12-24 months left) and "
            f"{_bold(int(df['Rolling Contract'].sum()))} are on rolling 12-month terms."
        )
        no_end = int((df["Urgency"] == "Unknown").sum())
        if no_end:
            points.append(f"{_bold(no_end)} account(s) have no contract end date on file - worth tidying in Zoho.")
        points.append(f"{_bold(int(df['New Deal'].sum()))} new account(s) signed in the last 30 days.")
        story.append(_callout(st, W, points))
        story.append(Spacer(1, 4 * mm))

        # contracts ending per month
        story.append(Paragraph("CONTRACTS ENDING PER MONTH  -  next 24 months (rolling contracts excluded)", st["lbl"]))
        story.append(Spacer(1, 1.5 * mm))
        dated = live[live["Days Remaining"].notna()]
        cols = [("Overdue", int((dated["Days Remaining"] < 0).sum()), "bad", "")]
        period0 = today_ts.to_period("M")
        for i in range(24):
            p = period0 + i
            in_month = dated["Contract End Date"].dt.to_period("M") == p
            n = int((in_month & (dated["Days Remaining"] >= 0)).sum()) if i == 0 else int(in_month.sum())
            sub = p.strftime("%Y") if (i == 0 or p.month == 1) else ""
            cols.append((p.strftime("%b"), n, "bad" if i < 12 else "warn", sub))
        story.append(_ColumnChart(W, cols))
        story.append(Paragraph(
            f'<font color="{_PDF["bad"]}">&#9632;</font> under 12 months (Red) &nbsp;&nbsp; '
            f'<font color="{_PDF["warn"]}">&#9632;</font> 12-24 months (Amber)', st["note"]))
        story.append(Spacer(1, 4 * mm))

        # watchlist
        vis = R["ren_visible"]
        story.append(Paragraph(f"RENEWAL WATCHLIST  -  soonest first ({len(vis)} account(s) match your filters)", st["lbl"]))
        story.append(Spacer(1, 1.5 * mm))
        if vis.empty:
            story.append(Paragraph("No accounts match the current filters.", st["note"]))
        else:
            shown = vis.head(12)
            rows, tints = [], {}
            for i, (_, r) in enumerate(shown.iterrows()):
                colour = {"Red": "bad", "Amber": "warn"}.get(r["Urgency"], "text")
                rows.append([
                    {"t": r["Account Name"], "bold": True}, {"t": r["Urgency"], "color": colour, "bold": True},
                    r["Time Remaining"], _fmt_date(r["Contract End Date"]), r["Primary Contact"], r["Primary Contact Number"],
                    format_handsets(r["No. of Handsets"]),
                ])
                if r["Urgency"] in ("Red", "Amber"):
                    tints[i] = _mix(colour, "surface" if i % 2 == 0 else "surface2", 0.12)
            story.append(_table(st, ["Account", "Urgency", "Time left", "Ends", "Contact", "Phone", "Handsets"], rows,
                                [46 * mm, 15 * mm, 24 * mm, 20 * mm, 30 * mm, 31 * mm, 16 * mm], right=(6,), row_tints=tints))
            if len(vis) > len(shown):
                story.append(Spacer(1, 1 * mm))
                story.append(Paragraph(f"Showing the soonest {len(shown)} of {len(vis)} - the full list is in the app.", st["note"]))
        story.append(Spacer(1, 5 * mm))

        # ---------------- 2. New accounts ----------------
        story.append(CondPageBreak(75 * mm))
        ns, ne = R["new_range"]
        story.append(_Section(W, 2, "New Accounts Added", f"Contracts signed {ns.strftime('%d/%m/%Y')} to {ne.strftime('%d/%m/%Y')} - for billing onboarding"))
        story.append(Spacer(1, 1.5 * mm))
        nt = R.get("new_table")
        if nt is None or len(nt) == 0:
            story.append(Paragraph("No contracts were signed in the selected date range.", st["note"]))
        else:
            if R.get("new_amounts_error"):
                story.append(Paragraph(
                    f'<font color="{_PDF["warn"]}">Amounts could not be read from the Zoho Legal Contracts for this report, so they show as "-".</font>', st["note"]))
                story.append(Spacer(1, 1 * mm))
            story.append(_callout(st, W, [
                f"{_bold(len(nt))} new account(s) signed in {_t(R.get('new_period', 'the period'))}, "
                f"total service value {_bold('£{:,.2f}'.format(R.get('new_total', 0)))}."
            ]))
            story.append(Spacer(1, 2.5 * mm))
            shown = nt.head(10)
            rows = [[{"t": r["Account Name"], "bold": True}, r["Account Owner"], r["Contract Signed Date"],
                     ("£{:,.2f}".format(r["Amount"]) if pd.notna(r["Amount"]) else "-")] for _, r in shown.iterrows()]
            story.append(_table(st, ["Account", "Owner", "Signed", "Amount"], rows,
                                [70 * mm, 46 * mm, 36 * mm, 30 * mm], right=(3,)))
            if len(nt) > len(shown):
                story.append(Spacer(1, 1 * mm))
                story.append(Paragraph(f"Showing the latest {len(shown)} of {len(nt)} - the full list is in the app.", st["note"]))
            oc = R.get("new_owner_counts")
            if oc is not None and len(oc):
                story.append(Spacer(1, 3 * mm))
                story.append(Paragraph("ACCOUNTS ADDED PER CONSULTANT", st["lbl"]))
                story.append(Spacer(1, 1 * mm))
                story.append(_BarList(W, [(k, int(v)) for k, v in oc.head(8).items()], color="accent", fmt=lambda v: f"{int(v)}"))
        story.append(Spacer(1, 4 * mm))

        # rolling
        rd = R["rolling_df"]
        story.append(Paragraph(f"ROLLING 12-MONTH CONTRACTS  -  {len(rd)} account(s)", st["lbl"]))
        story.append(Spacer(1, 1.5 * mm))
        if rd.empty:
            story.append(Paragraph("No rolling contract accounts.", st["note"]))
        else:
            shown = rd.head(6)
            rows = [[{"t": r["Account Name"], "bold": True}, r["Time Remaining"], _fmt_date(r["Contract End Date"]),
                     r["Primary Contact"], r["Primary Contact Number"]] for _, r in shown.iterrows()]
            story.append(_table(st, ["Account", "Time left", "Ends", "Contact", "Phone"], rows,
                                [60 * mm, 28 * mm, 24 * mm, 36 * mm, 34 * mm]))
            if len(rd) > len(shown):
                story.append(Spacer(1, 1 * mm))
                story.append(Paragraph(f"Showing {len(shown)} of {len(rd)} - the full list is in the app.", st["note"]))
        story.append(Spacer(1, 6 * mm))

        # ---------------- 3. Sales pipeline ----------------
        story.append(CondPageBreak(110 * mm))
        S = R.get("sales")
        if S is None:
            story.append(_Section(W, 3, "Sales Pipeline", "Deals feed unavailable"))
            story.append(Paragraph("The deals could not be loaded from Zoho when this report was made.", st["note"]))
        else:
            story.append(_Section(W, 3, "Sales Pipeline",
                                  f"{S['timeframe']}  -  Consultant: {S['rep']}  -  Stage: {S['status']}"))
            story.append(Spacer(1, 1.5 * mm))
            k = [("Deals in view", S["total"], ""), ("New / booked appts", S["early"], "warn"),
                 ("In progress / closing", S["active"], "cyan"), ("Won / closed", f"{S['won']} won - {S['lost']} lost", "good")]
            story.append(_KpiRow(W, k))
            if S["show_fin"]:
                story.append(Spacer(1, 3 * mm))
                story.append(_KpiRow(W, [("Pipeline lease value", gbp(S["fin_pipeline"]), ""),
                                         ("Won lease value", gbp(S["fin_won"]), "good"),
                                         ("Won monthly network spend", gbp(S["fin_network"]), "good")]))
            story.append(Spacer(1, 3.5 * mm))

            pts = []
            if S["total"]:
                pts.append(f"{_bold(S['total'])} deal(s) in {_t(S['timeframe'])}: {_bold(S['won'])} won, {_bold(S['lost'])} lost, "
                           f"{_bold(S['active'])} in progress and {_bold(S['early'])} at the booked-appointment stage.")
            else:
                pts.append(f"No deals match {_t(S['timeframe'])} with the current filters.")
            top = S.get("top_rep")
            if top:
                pts.append(f"Top consultant by deals won: {_bold(top[0])} with {_bold(top[1])}.")
            up = S.get("upcoming")
            if up is not None and len(up):
                nxt = up.iloc[0]
                pts.append(f"Next appointment: {_bold(nxt['Client Name'])} with {_t(nxt['Sales Rep'] or 'Unassigned')} "
                           f"on {nxt['Parsed Date'].strftime('%a %d %b at %H:%M')}.")
            sd = R.get("sold")
            if sd and sd.get("df") is not None and len(sd["df"]):
                pts.append(f"{_bold(len(sd['df']))} deal(s) closed won {sd['range'][0].strftime('%d/%m')} to "
                           f"{sd['range'][1].strftime('%d/%m/%Y')}, worth {_bold('£{:,.2f}'.format(sd['total']))} in lease value.")
            story.append(_callout(st, W, pts))
            story.append(Spacer(1, 4 * mm))

            # two charts side by side
            half = (W - 6 * mm) / 2
            won_rows = [(k_, int(v)) for k_, v in S["won_by_rep"].items()][:8]
            left = [Paragraph("DEALS WON PER CONSULTANT", st["lbl"]), Spacer(1, 1.5 * mm)]
            left.append(_BarList(half, won_rows, color="good", label_w=30 * mm, fmt=lambda v: f"{int(v)}")
                        if won_rows else Paragraph("No won deals in this timeframe.", st["note"]))
            stage_rows = [(s["Stage / Status"], s["Total Count"], s["color"]) for s in S["stages"] if s["Total Count"] > 0]
            right = [Paragraph("STAGE BREAKDOWN", st["lbl"]), Spacer(1, 1.5 * mm)]
            right.append(_BarList(half, stage_rows, color="accent", label_w=34 * mm, fmt=lambda v: f"{int(v)}")
                         if stage_rows else Paragraph("No deals in this timeframe.", st["note"]))
            pair, _ = _pair(left, right, W)
            story.append(pair)
            story.append(Spacer(1, 4 * mm))

            # consultant performance
            rs = S["rep_summary"]
            if rs is not None and len(rs):
                story.append(Paragraph("CONSULTANT PERFORMANCE  -  whole timeframe", st["lbl"]))
                story.append(Spacer(1, 1.5 * mm))
                rows = [[{"t": r["Sales Rep"] or "Unassigned", "bold": True}, int(r["Total Deals"]), int(r["Won"]),
                         int(r["In Progress"]), int(r["Booked"]), int(r["Lost"])] for _, r in rs.head(10).iterrows()]
                story.append(_table(st, ["Consultant", "Total", "Won", "In progress", "Booked", "Lost"], rows,
                                    [66 * mm, 22 * mm, 22 * mm, 26 * mm, 24 * mm, 22 * mm], right=(1, 2, 3, 4, 5)))
                story.append(Spacer(1, 4 * mm))

            # upcoming appointments
            if up is not None and len(up):
                story.append(CondPageBreak(45 * mm))
                story.append(Paragraph("UPCOMING APPOINTMENTS  -  next 10 (follows consultant and stage filters)", st["lbl"]))
                story.append(Spacer(1, 1.5 * mm))
                rows = [[r["Parsed Date"].strftime("%a %d %b  %H:%M"), {"t": r["Client Name"], "bold": True},
                         r["Sales Rep"] or "Unassigned", r["Status"]] for _, r in up.iterrows()]
                story.append(_table(st, ["When", "Client", "Consultant", "Stage"], rows,
                                    [36 * mm, 66 * mm, 40 * mm, 40 * mm]))
                story.append(Spacer(1, 4 * mm))

            # sold deals
            if sd and sd.get("df") is not None and len(sd["df"]):
                story.append(CondPageBreak(55 * mm))
                scope = "SYComms-owned deals only" if sd["syc_only"] else "all Closed Won deals in Zoho"
                story.append(Paragraph(f"SOLD DEALS  -  closed won {sd['range'][0].strftime('%d/%m/%Y')} to "
                                       f"{sd['range'][1].strftime('%d/%m/%Y')} ({scope})", st["lbl"]))
                story.append(Spacer(1, 1.5 * mm))
                sdf = sd["df"]
                rows = [[{"t": r["Client Name"], "bold": True}, r["Sales Rep"] or "Unassigned",
                         _fmt_date(r["Closing Date"]), "£{:,.2f}".format(r["Monthly Network Spend"]),
                         "£{:,.2f}".format(r["Total Lease Value"])] for _, r in sdf.head(8).iterrows()]
                story.append(_table(st, ["Deal", "Consultant", "Closed", "Monthly network", "Lease value"], rows,
                                    [58 * mm, 36 * mm, 24 * mm, 32 * mm, 32 * mm], right=(3, 4)))
                story.append(Spacer(1, 1 * mm))
                extra = f"Showing the latest {min(8, len(sdf))} of {len(sdf)}.  " if len(sdf) > 8 else ""
                story.append(Paragraph(f"{extra}Total lease value sold this period: {_bold('£{:,.2f}'.format(sd['total']))}.", st["note"]))

        A = R.get("assessment")
        if A:
            story.append(PageBreak())
            story += _assessment_story(A, st, W, 4)

        return _render_pdf(story, "SYComms Renewals & Sales Briefing")


# --- PDF briefing download (sidebar) ---
if REPORTLAB_OK:
    try:
        pdf_bytes = build_pdf_report(
            {
                "generated": datetime.now(UK_TZ).strftime("%A %d %B %Y, %H:%M (UK time)"),
                "df": df,
                "today": today,
                **report,
            }
        )
        pdf_slot.download_button(
            "Download PDF briefing",
            data=pdf_bytes,
            file_name=f"SYComms_Renewals_Sales_Briefing_{datetime.now(UK_TZ).strftime('%Y-%m-%d')}.pdf",
            mime="application/pdf",
            key="pdf_download",
            help="A 2-3 page summary of the Renewals and Sales tabs (plus an Assessment page when a person is chosen on the Assessment tab), following the filters and date ranges currently selected.",
            **FULL_WIDTH,
        )
    except Exception as pdf_err:  # never let the report take the dashboard down
        pdf_slot.caption(f"PDF briefing unavailable: {pdf_err}")
else:
    pdf_slot.caption("PDF briefing needs the reportlab package - add `reportlab` to requirements.txt.")

# --- Assessment PDF (inside the Assessment tab) ---
if asm_pdf_slot is not None and report.get("assessment"):
    if REPORTLAB_OK:
        try:
            _A = report["assessment"]
            asm_pdf_slot.download_button(
                "Download assessment PDF",
                data=build_assessment_pdf({"generated": datetime.now(UK_TZ).strftime("%A %d %B %Y, %H:%M (UK time)"), "assessment": _A}),
                file_name=f"Assessment_{re.sub(r'[^A-Za-z0-9]+', '_', _A['person']).strip('_')}_{re.sub(r'[^A-Za-z0-9]+', '_', _A['label']).strip('_')}.pdf",
                mime="application/pdf",
                key="asm_pdf_download",
                help="A one-person assessment page: deals, calls and activity for the period selected above.",
            )
        except Exception as pdf_err:
            asm_pdf_slot.caption(f"Assessment PDF unavailable: {pdf_err}")
    else:
        asm_pdf_slot.caption("PDF export needs the reportlab package - add `reportlab` to requirements.txt.")

# Fill in the hero banner reserved at the top of the page now that the
# live counts are known.
render_hero(hero_placeholder, len(df), len(pipeline_df) if not deals_error else 0)
