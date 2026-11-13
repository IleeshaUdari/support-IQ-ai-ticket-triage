"""SupportIQ Enterprise Operations UI.

Run from the project root:
    python -m streamlit run dashboard/streamlit_app.py

Uses the existing dashboard.api_client.SupportIQClient and FastAPI backend.
No direct pandas dependency. Demo mode uses clearly labeled synthetic tickets; Live mode uses the real backend.
"""
from __future__ import annotations

import html
import math
import sys
import random
from copy import deepcopy
from datetime import timedelta
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from dashboard.api_client import APIError, SupportIQClient

st.set_page_config(
    page_title="SupportIQ | Intelligence Operations",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

CATEGORIES = ("billing", "delivery", "account", "technical")
PRIORITIES = ("low", "medium", "high")
STATUSES = ("open", "pending_review", "resolved")
COLORS = {"billing": "#6E9CFF", "delivery": "#A48AFF", "account": "#29C8C2", "technical": "#F0B76B"}
PRIORITY_COLORS = {"high": "#FB7185", "medium": "#F5B84D", "low": "#34D399"}
STATUS_COLORS = {"open": "#60A5FA", "pending_review": "#FBBF24", "resolved": "#34D399"}
PAGES = (
    "Command Center", "Ticket Management", "AI Intelligence",
    "Human Review", "Audit History", "New Ticket",
)
PAGE_ICONS = {"Command Center": "◈", "Ticket Management": "▤", "AI Intelligence": "✧", "Human Review": "◇", "Audit History": "◷", "New Ticket": "+"}

CSS = r"""
<style>
:root {color-scheme:dark;}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {background:#0B1120!important;color:#E8EFFB!important;}
[data-testid="stHeader"] {background:rgba(11,17,32,.92)!important;}
[data-testid="stSidebar"] {background:#0D1729!important;border-right:1px solid #223047!important;}
[data-testid="stSidebar"] * {color:#DCE7F8;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {color:#DCE7F8;}
.block-container {max-width:1580px!important;padding-top:2.2rem!important;padding-bottom:4rem!important;}
h1,h2,h3,h4,p,span,div {font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;}
h1 {font-size:2rem!important;letter-spacing:-.045em!important;color:#F7FAFF!important;}
h2,h3 {color:#F0F5FF!important;letter-spacing:-.03em!important;}
[data-testid="stCaptionContainer"],small {color:#95A5BE!important;}
[data-testid="stMetric"] {background:#121F33;border:1px solid #253650;border-radius:15px;padding:18px 20px;}
[data-testid="stMetricLabel"] {color:#A8B8D0!important;}
[data-testid="stMetricValue"] {color:#F6F9FF!important;}
[data-testid="stMetricDelta"] {color:#8E9FB8!important;}
[data-testid="stVerticalBlockBorderWrapper"] {border-color:#26354D!important;}
[data-testid="stExpander"] {background:#121E31;border:1px solid #25354C;border-radius:12px;}
[data-testid="stExpander"] summary {color:#E8F0FC!important;}
.stButton>button, .stFormSubmitButton>button {border-radius:10px!important;border:1px solid #344765!important;background:#182B46!important;color:#F5F8FF!important;font-weight:650!important;min-height:40px;}
.stButton>button:hover,.stFormSubmitButton>button:hover {border-color:#6B9EFF!important;background:#203A5F!important;color:#FFF!important;}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"] {background:#397BE7!important;border-color:#397BE7!important;color:#FFF!important;}
[data-testid="stSidebar"] .stButton>button {background:#1A3152!important;color:#E9F3FF!important;border:1px solid #355279!important;}
[data-testid="stSidebar"] [role="radiogroup"] label {border-radius:9px;padding:7px 9px;margin:2px 0;}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {background:#1B2D49;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background:#214578;}
[data-testid="stSidebar"] [role="radiogroup"] label p {font-size:.92rem!important;}
[data-testid="stSidebar"] [role="radiogroup"] [data-testid="stWidgetLabel"] {display:none;}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stNumberInput"] input {background:#111E32!important;color:#F4F8FF!important;border-color:#34455F!important;}
[data-baseweb="select"]>div {background:#111E32!important;color:#F4F8FF!important;border-color:#34455F!important;}
[data-baseweb="select"] span {color:#F4F8FF!important;}
[data-testid="stProgress"]>div>div {background:#1D2B40!important;}
[data-testid="stProgress"]>div>div>div {background:#538FF4!important;}
hr {border-color:#25354A!important;}
.siq-hero {padding:12px 0 21px;display:flex;align-items:center;justify-content:space-between;gap:12px;}
.siq-eyebrow {color:#79A9FF;font-size:11px;font-weight:800;letter-spacing:.17em;text-transform:uppercase;}
.siq-title {font-size:32px;font-weight:800;letter-spacing:-.045em;line-height:1.25;color:#F7FAFF;margin:7px 0;}
.siq-subtitle {color:#91A2BC;font-size:13px;}
.siq-pill {display:inline-block;padding:5px 10px;border-radius:99px;background:#183B34;border:1px solid #276655;color:#79E1B6;font-size:11px;font-weight:750;}
.siq-brand {display:flex;align-items:center;gap:12px;margin:15px 0 5px;}
.siq-logo {width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,#3A82F6,#7856DE);display:grid;place-items:center;font-size:21px;}
.siq-brand-name {font-weight:800;font-size:19px;color:#FFF;letter-spacing:-.04em;}
.siq-brand-sub {font-size:10px;color:#8197B8;letter-spacing:.13em;font-weight:700;}
.siq-section {display:flex;align-items:center;justify-content:space-between;margin:12px 0 15px;}
.siq-section-title {font-size:16px;font-weight:800;color:#F4F7FF;letter-spacing:-.02em;}
.siq-muted {color:#91A2BB;font-size:12px;}
.siq-card {background:#121F33;border:1px solid #26364F;border-radius:15px;padding:20px;min-height:100%;}
.siq-kpi-label {font-size:11px;color:#A0B0C9;font-weight:700;letter-spacing:.045em;text-transform:uppercase;}
.siq-kpi-value {font-size:31px;color:#F8FAFF;font-weight:800;letter-spacing:-.05em;margin:10px 0 4px;}
.siq-kpi-foot {font-size:11px;color:#8398B5;}
.siq-kpi-icon {float:right;color:#78A8FF;font-size:20px;}
.siq-tag {display:inline-block;border-radius:6px;padding:4px 8px;font-size:10px;font-weight:800;letter-spacing:.01em;white-space:nowrap;}
.siq-table-wrap {overflow-x:auto;border:1px solid #283951;border-radius:12px;background:#111D30;}
.siq-table {width:100%;border-collapse:collapse;font-size:12px;color:#E1EAF8;min-width:680px;}
.siq-table th {text-align:left;color:#8299B8;background:#16243A;font-size:10px;letter-spacing:.075em;text-transform:uppercase;padding:13px 12px;font-weight:800;}
.siq-table td {border-top:1px solid #25354A;padding:12px;vertical-align:middle;}
.siq-table tr:hover td {background:#18283F;}
.siq-bar-row {margin:12px 0;}
.siq-bar-head {display:flex;justify-content:space-between;font-size:12px;color:#B9C7DA;margin-bottom:7px;}
.siq-bar-track {height:8px;background:#26364C;border-radius:99px;overflow:hidden;}
.siq-bar-fill {height:100%;border-radius:99px;}
.siq-donut {width:152px;height:152px;border-radius:50%;position:relative;flex-shrink:0;}
.siq-donut:after {content:"";position:absolute;inset:27px;border-radius:50%;background:#121F33;}
.siq-donut-wrap {display:flex;align-items:center;justify-content:center;gap:25px;flex-wrap:wrap;min-height:185px;}
.siq-legend {min-width:160px;flex:1;}
.siq-legend-row {display:flex;align-items:center;justify-content:space-between;gap:12px;color:#B6C5D9;font-size:12px;margin:12px 0;}
.siq-dot {width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:7px;}
.siq-note {background:#13253C;border:1px solid #284464;border-radius:12px;padding:13px 15px;color:#AFC6E5;font-size:12px;}
.siq-empty {padding:26px 15px;text-align:center;color:#95A8C3;border:1px dashed #34465D;border-radius:12px;background:#111D30;}
.siq-statline {display:flex;align-items:center;justify-content:space-between;padding:9px 0;border-bottom:1px solid #23344A;color:#BCCBE0;font-size:12px;}
.siq-statline:last-child {border-bottom:0;}
.siq-statline strong {color:#F1F5FC;}
.siq-timeline {border-left:2px solid #355B92;margin-left:7px;padding:2px 0 8px 18px;}
.siq-timeline-item {position:relative;margin:0 0 17px;color:#AFC0D8;font-size:12px;}
.siq-timeline-item:before {content:"";position:absolute;left:-25px;top:3px;width:11px;height:11px;background:#5797F8;border:3px solid #121F33;border-radius:50%;}
@media(max-width:850px){.siq-title{font-size:26px}.block-container{padding-left:1rem!important;padding-right:1rem!important}.siq-donut{width:128px;height:128px}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# High-contrast theme overrides. Native Streamlit widgets remain accessible and clickable.
ACCESSIBLE_CSS = r"""
<style>
:root {color-scheme:dark;}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stAppViewBlockContainer"] {background:#0A1324!important;color:#F3F7FF!important;}
[data-testid="stSidebar"] {background:#101D33!important;border-right:1px solid #334766!important;}
[data-testid="stSidebar"] *, [data-testid="stSidebar"] p {color:#F0F5FF!important;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background:#2C538C!important;border:1px solid #548BE0!important;}
[data-testid="stSidebar"] [role="radiogroup"] label:not(:has(input:checked)) {border:1px solid transparent!important;}
[data-testid="stSidebar"] .stButton button {background:#284B7B!important;color:#FFFFFF!important;border-color:#6092D7!important;}
[data-testid="stSidebar"] .stButton button:hover {background:#3567A9!important;}
[data-testid="stWidgetLabel"] p, label, [data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {color:#E9F1FF;}
[data-testid="stCaptionContainer"] p {color:#B6C7DF!important;}
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea,
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {background:#172840!important;color:#FFFFFF!important;border:1px solid #5A7194!important;caret-color:#FFFFFF!important;}
input::placeholder,textarea::placeholder {color:#B4C5DC!important;opacity:1!important;}
[data-baseweb="select"] > div, [data-baseweb="select"] input {background:#172840!important;color:#FFFFFF!important;border-color:#5A7194!important;}
[data-baseweb="select"] span, [data-baseweb="select"] svg {color:#F0F6FF!important;fill:#F0F6FF!important;}
[data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"], [role="option"] {background:#192B45!important;color:#F4F7FF!important;}
[role="option"]:hover, [aria-selected="true"][role="option"] {background:#305688!important;}
[data-testid="stSelectbox"] label, [data-testid="stTextInput"] label,
[data-testid="stTextArea"] label, [data-testid="stCheckbox"] label,
[data-testid="stToggle"] label, [data-testid="stNumberInput"] label {color:#EFF5FF!important;}
[data-testid="stExpander"] {background:#14233A!important;border:1px solid #3B506D!important;}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p {color:#F5F8FF!important;}
[data-testid="stAlert"] {border-radius:12px!important;}
[data-testid="stAlert"] p {color:inherit!important;}
[data-testid="stForm"] {background:#121F34!important;border:1px solid #334866!important;border-radius:16px!important;padding:20px!important;}
.stButton button, .stFormSubmitButton button {color:#FFFFFF!important;background:#24446E!important;border:1px solid #567CAC!important;}
.stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"] {background:#3D82EE!important;border-color:#6AA2FF!important;}
.stButton button:focus-visible, input:focus-visible, textarea:focus-visible {outline:2px solid #93C5FD!important;outline-offset:2px!important;}
.siq-kpi-foot {color:#B8C9DF!important;}
.siq-muted, .siq-subtitle {color:#C1D0E5!important;}
.siq-card {background:linear-gradient(145deg,#182A43,#142239)!important;border:1px solid #344B69!important;box-shadow:0 9px 25px rgba(0,0,0,.13);}
.siq-kpi-label {color:#C4D3E8!important;}
.siq-kpi-value {color:#FFFFFF!important;}
.siq-table-wrap {border-color:#405675!important;}
.siq-table th {color:#CFDDF0!important;background:#1D314D!important;}
.siq-table td {color:#EAF1FF!important;}
.siq-statline {color:#D7E3F4!important;}
.siq-statline strong {color:#FFFFFF!important;}
.siq-legend-row,.siq-bar-head {color:#E4EEFC!important;}
.siq-note {color:#D9E8FA!important;}
.siq-hero {padding-bottom:24px;}
.siq-pill.demo {background:#3A2D17;border-color:#946D27;color:#FFE2A0;}
.siq-demo-banner {background:#243653;border:1px solid #5579A8;color:#EAF2FF;border-radius:12px;padding:12px 17px;margin:3px 0 19px;font-size:12px;line-height:1.6;}
.siq-demo-banner strong {color:#FFFFFF;}
.siq-table td:nth-child(2) {max-width:350px;}
@media (max-width:1100px) {.siq-card {padding:14px!important}.siq-kpi-value {font-size:25px!important}}
</style>
"""
st.markdown(ACCESSIBLE_CSS, unsafe_allow_html=True)




# -----------------------------------------------------------------------------
# Demo dataset: deterministic, synthetic, and kept strictly in Streamlit session.
# Switching to Live mode never writes demo tickets into the actual SQLite DB.
# -----------------------------------------------------------------------------
DEMO_MESSAGES = {
    "billing": [
        "I was charged twice for my subscription this month. Please refund the duplicate payment.",
        "My invoice shows the wrong amount and I need it corrected before payment.",
        "The payment went through but the receipt has not arrived.",
        "I canceled my plan but was billed again yesterday.",
        "Can you explain the annual renewal charges on my invoice?",
        "I need a refund for a subscription I did not intend to renew.",
        "The checkout payment failed but the money was deducted from my card.",
        "Please update the billing address shown on my next invoice.",
    ],
    "delivery": [
        "My package is three days late and tracking has stopped updating.",
        "The order arrived with one item missing from the box.",
        "I received the wrong product and need an exchange.",
        "The tracking page says delivered but nothing arrived at my address.",
        "Please change the delivery address before dispatch.",
        "The courier left my parcel at the wrong location.",
        "The product arrived damaged and the packaging was torn.",
        "I need an estimated arrival date for my replacement order.",
    ],
    "account": [
        "I cannot sign in even after resetting my password twice.",
        "Please help me enable two-factor authentication on my account.",
        "My account was locked after several failed login attempts.",
        "I need to change the email address associated with my profile.",
        "I am not receiving the account verification email.",
        "Please deactivate an old account that I no longer use.",
        "I noticed an unfamiliar login and want to secure my account.",
        "My profile settings do not save after I update them.",
    ],
    "technical": [
        "The dashboard crashes whenever I upload a PDF document.",
        "The mobile app freezes on the loading screen after the latest update.",
        "Our API requests are returning intermittent 500 errors.",
        "Exporting a CSV file produces an empty download.",
        "The search feature is slow and sometimes times out.",
        "Notifications are not appearing in the application.",
        "The integration stopped syncing data overnight.",
        "The settings page displays an error after I save changes.",
    ],
}
DEMO_TEAMS = {
    "billing": "Payments Team", "delivery": "Fulfillment Team",
    "account": "Account Support", "technical": "Technical Support",
}
DEMO_REASONS = [
    "Low prediction confidence; manual verification recommended.",
    "Potential customer-impacting issue; manual review recommended.",
    "Routine request; normal triage path.",
    "Sensitive account or payment issue; human review required.",
]


def demo_seed() -> None:
    if "siq_demo_tickets" in st.session_state:
        return
    rng = random.Random(20261113)
    now = datetime.now(timezone.utc)
    tickets = []
    statuses = ("open", "pending_review", "resolved")
    priorities = ("low", "medium", "high")
    for i in range(72):
        category = CATEGORIES[i % len(CATEGORIES)]
        message = DEMO_MESSAGES[category][(i // len(CATEGORIES)) % 8]
        priority = priorities[(i * 7 + 1) % 3]
        status = statuses[(i * 5 + (i // 6)) % 3]
        confidence = round(rng.uniform(.49, .98), 3)
        needs_review = confidence < .60 or status == "pending_review" or (i % 13 == 0)
        ticket_id = f"DEMO-{i+1:04d}"
        created = (now - timedelta(hours=i * 2 + rng.randint(0, 4))).isoformat()
        tickets.append({
            "ticket_id": ticket_id,
            "message": message,
            "category": category,
            "priority": priority,
            "status": status,
            "created_at": created,
            "decision": {
                "category": category,
                "confidence": confidence,
                "assigned_team": DEMO_TEAMS[category],
                "needs_human_review": needs_review,
                "reason": DEMO_REASONS[i % len(DEMO_REASONS)],
                "model_version": "demo-simulated-v1",
            },
        })
    st.session_state["siq_demo_tickets"] = tickets
    st.session_state["siq_demo_reviews"] = {}
    st.session_state["siq_demo_counter"] = 72


class DemoClient:
    """API-compatible in-memory demo adapter. Does not call or mutate FastAPI."""

    def __init__(self) -> None:
        demo_seed()

    def health(self) -> dict:
        return {"status": "healthy", "model_loaded": True, "mode": "demo"}

    def get_all_tickets(self, status=None) -> list[dict]:
        tickets = st.session_state["siq_demo_tickets"]
        if status:
            tickets = [t for t in tickets if t.get("status") == status]
        return deepcopy(tickets)

    def get_ticket(self, ticket_id: str) -> dict:
        for ticket in st.session_state["siq_demo_tickets"]:
            if ticket["ticket_id"] == ticket_id:
                return deepcopy(ticket)
        raise ValueError("Demo ticket not found")

    def create_ticket(self, message: str) -> dict:
        message = message.strip()
        if len(message) < 5:
            raise ValueError("Please enter a longer ticket message")
        st.session_state["siq_demo_counter"] += 1
        n = st.session_state["siq_demo_counter"]
        lowered = message.lower()
        keywords = {
            "billing": ("charge", "invoice", "refund", "payment", "bill", "subscription"),
            "delivery": ("deliver", "order", "parcel", "shipping", "courier", "package"),
            "account": ("account", "login", "password", "sign in", "profile", "verification"),
            "technical": ("error", "crash", "api", "bug", "upload", "app", "website"),
        }
        category = next((k for k, words in keywords.items() if any(w in lowered for w in words)), "technical")
        priority = "high" if any(w in lowered for w in ("urgent", "fraud", "charged twice", "hacked", "security")) else "medium"
        ticket = {
            "ticket_id": f"DEMO-{n:04d}", "message": message,
            "category": category, "priority": priority, "status": "pending_review",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "decision": {
                "category": category, "confidence": .68,
                "assigned_team": DEMO_TEAMS[category], "needs_human_review": True,
                "reason": "Illustrative demo rules; not an actual ML prediction.",
                "model_version": "demo-simulated-v1",
            },
        }
        st.session_state["siq_demo_tickets"].insert(0, ticket)
        return deepcopy(ticket)

    def review_ticket(self, ticket_id: str, category: str, priority: str, status: str, reviewer_note: str) -> dict:
        tickets = st.session_state["siq_demo_tickets"]
        for ticket in tickets:
            if ticket["ticket_id"] == ticket_id:
                records = st.session_state["siq_demo_reviews"].setdefault(ticket_id, [])
                record = {
                    "id": len(records) + 1,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "previous_category": ticket["category"], "new_category": category,
                    "previous_priority": ticket["priority"], "new_priority": priority,
                    "previous_status": ticket["status"], "new_status": status,
                    "reviewer_note": reviewer_note,
                }
                records.insert(0, record)
                ticket.update(category=category, priority=priority, status=status)
                return deepcopy(ticket)
        raise ValueError("Demo ticket not found")

    def get_reviews(self, ticket_id: str) -> dict:
        return {"reviews": deepcopy(st.session_state["siq_demo_reviews"].get(ticket_id, []))}


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else "—"), quote=True)


def nice(value: Any) -> str:
    return str(value or "unknown").replace("_", " ").title()


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def decision_of(ticket: dict) -> dict:
    value = ticket.get("decision")
    return value if isinstance(value, dict) else {}


def confidence_of(ticket: dict) -> float:
    decision = decision_of(ticket)
    return max(0.0, min(1.0, safe_float(decision.get("confidence", 0))))


def flagged(ticket: dict) -> bool:
    return bool(decision_of(ticket).get("needs_human_review", False))


def badge(value: str, color: str) -> str:
    return (f'<span class="siq-tag" style="background:{color}22;'
            f'color:{color};border:1px solid {color}55">{esc(nice(value))}</span>')


def card(content: str) -> str:
    return f'<div class="siq-card">{content}</div>'


def section(title: str, sub: str = "") -> None:
    st.markdown(
        f'<div class="siq-section"><span class="siq-section-title">{esc(title)}</span>'
        f'<span class="siq-muted">{esc(sub)}</span></div>',
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, eyebrow: str = "OPERATIONS / WORKSPACE") -> None:
    st.markdown(
        f'<div class="siq-hero"><div><div class="siq-eyebrow">{esc(eyebrow)}</div>'
        f'<div class="siq-title">{esc(title)}</div>'
        f'<div class="siq-subtitle">{esc(subtitle)}</div></div>'
        f'<span class="siq-pill {"demo" if st.session_state.get("siq_mode") == "Demo (sample data)" else ""}">{"◆ DEMO DATA" if st.session_state.get("siq_mode") == "Demo (sample data)" else "● API CONNECTED"}</span></div>',
        unsafe_allow_html=True,
    )


def kpi(label: str, value: str, foot: str, icon: str = "◈") -> None:
    st.markdown(card(
        f'<span class="siq-kpi-icon">{esc(icon)}</span>'
        f'<div class="siq-kpi-label">{esc(label)}</div>'
        f'<div class="siq-kpi-value">{esc(value)}</div>'
        f'<div class="siq-kpi-foot">{esc(foot)}</div>'
    ), unsafe_allow_html=True)


def bar(label: str, count: int, total: int, color: str) -> str:
    pct = 100 * count / total if total else 0
    return (
        '<div class="siq-bar-row"><div class="siq-bar-head">'
        f'<span>{esc(nice(label))}</span><strong>{count} · {pct:.0f}%</strong></div>'
        '<div class="siq-bar-track">'
        f'<div class="siq-bar-fill" style="width:{pct:.2f}%;background:{color}"></div>'
        '</div></div>'
    )


def donut(counts: Counter, palette: dict, total: int) -> str:
    if not total:
        return '<div class="siq-empty">No ticket data yet</div>'
    angle = 0.0
    stops = []
    legend = []
    for key, count in counts.most_common():
        color = palette.get(key, "#64748B")
        end = angle + count * 100 / total
        stops.append(f"{color} {angle:.3f}% {end:.3f}%")
        legend.append(
            f'<div class="siq-legend-row"><span><i class="siq-dot" '
            f'style="background:{color}"></i>{esc(nice(key))}</span>'
            f'<strong>{count} ({count / total:.0%})</strong></div>'
        )
        angle = end
    return (
        '<div class="siq-donut-wrap">'
        f'<div class="siq-donut" style="background:conic-gradient({", ".join(stops)})"></div>'
        f'<div class="siq-legend">{"".join(legend)}</div></div>'
    )


def render_table(tickets: list[dict], max_rows: int | None = None) -> None:
    rows = tickets if max_rows is None else tickets[:max_rows]
    if not rows:
        st.markdown('<div class="siq-empty">No matching tickets found.</div>', unsafe_allow_html=True)
        return
    body = []
    for t in rows:
        category = str(t.get("category", "unknown")).lower()
        priority = str(t.get("priority", "unknown")).lower()
        status = str(t.get("status", "unknown")).lower()
        message = str(t.get("message", ""))
        short = message[:90] + ("…" if len(message) > 90 else "")
        body.append(
            "<tr>"
            f'<td><strong>{esc(t.get("ticket_id", "—"))}</strong></td>'
            f'<td title="{esc(message)}">{esc(short)}</td>'
            f'<td>{badge(category, COLORS.get(category, "#94A3B8"))}</td>'
            f'<td>{badge(priority, PRIORITY_COLORS.get(priority, "#94A3B8"))}</td>'
            f'<td>{badge(status, STATUS_COLORS.get(status, "#94A3B8"))}</td>'
            f'<td>{confidence_of(t):.0%}</td>'
            "</tr>"
        )
    st.markdown(
        '<div class="siq-table-wrap"><table class="siq-table"><thead><tr>'
        '<th>Ticket ID</th><th>Customer Message</th><th>Category</th>'
        '<th>Priority</th><th>Status</th><th>AI Score</th>'
        f'</tr></thead><tbody>{"".join(body)}</tbody></table></div>',
        unsafe_allow_html=True,
    )


def details(ticket: dict) -> None:
    d = decision_of(ticket)
    section("Ticket Details", str(ticket.get("ticket_id", "")))
    st.markdown(card(
        '<div class="siq-kpi-label">CUSTOMER MESSAGE</div>'
        f'<div style="color:#F2F6FD;font-size:14px;line-height:1.7;margin-top:9px">'
        f'{esc(ticket.get("message", ""))}</div>'
    ), unsafe_allow_html=True)
    st.write("")
    a, b, c, e = st.columns(4)
    with a: kpi("Category", nice(ticket.get("category")), "Current ticket category", "▤")
    with b: kpi("Priority", nice(ticket.get("priority")), "Current priority", "!")
    with c: kpi("Status", nice(ticket.get("status")), "Current workflow state", "◷")
    with e: kpi("AI Confidence", f"{confidence_of(ticket):.1%}", "Model score", "✧")
    st.write("")
    rows = [
        ("Original AI category", nice(d.get("category"))),
        ("Assigned team", nice(d.get("assigned_team"))),
        ("Human review flag", "Yes" if flagged(ticket) else "No"),
        ("Model version", str(d.get("model_version", "Not available"))),
        ("Decision reason", str(d.get("reason", "Not available"))),
    ]
    st.markdown(card("".join(
        f'<div class="siq-statline"><span>{esc(label)}</span><strong>{esc(value)}</strong></div>'
        for label, value in rows
    )), unsafe_allow_html=True)
    if str(ticket.get("category", "")).lower() != str(d.get("category", "")).lower():
        st.info("Current ticket category differs from the original AI prediction; a reviewer may have changed it.")


def request(method, *args, **kwargs):
    try:
        return method(*args, **kwargs)
    except APIError as exc:
        st.error(f"Backend request failed: {exc}")
    except Exception as exc:
        # Avoid exposing implementation paths or potentially sensitive details in the UI.
        st.error(f"Unexpected dashboard error ({type(exc).__name__}). Check the application logs.")
    return None


def get_tickets(client: SupportIQClient) -> list[dict] | None:
    result = request(client.get_all_tickets)
    if result is None:
        return None
    if isinstance(result, list):
        return [t for t in result if isinstance(t, dict)]
    if isinstance(result, dict) and isinstance(result.get("tickets"), list):
        return [t for t in result["tickets"] if isinstance(t, dict)]
    st.error("Unexpected ticket-list response from the backend.")
    return None


def overview(tickets: list[dict]) -> None:
    hero("Intelligence Command Center", "Live ticket operations, AI decisions and human oversight", "SUPPORTIQ / COMMAND CENTER")
    total = len(tickets)
    pending = sum(t.get("status") == "pending_review" for t in tickets)
    high = sum(t.get("priority") == "high" for t in tickets)
    resolved = sum(t.get("status") == "resolved" for t in tickets)
    flagged_count = sum(flagged(t) for t in tickets)
    cols = st.columns(5, gap="small")
    cards = [
        ("Total Tickets", str(total), "Stored support requests", "▤"),
        ("Pending Review", str(pending), "Awaiting human action", "◇"),
        ("High Priority", str(high), "Urgent ticket workload", "!"),
        ("Resolved", str(resolved), "Completed tickets", "✓"),
        ("AI Flag Rate", f"{flagged_count / total:.0%}" if total else "0%", "Flagged by AI decision rules", "✧"),
    ]
    for col, data in zip(cols, cards):
        with col: kpi(*data)
    st.write("")
    left, right = st.columns([1.05, 1], gap="medium")
    with left:
        section("Ticket Categories", "Current distribution")
        st.markdown(card(donut(Counter(str(t.get("category", "unknown")) for t in tickets), COLORS, total)), unsafe_allow_html=True)
    with right:
        section("Priority Breakdown", "Live ticket mix")
        counts = Counter(str(t.get("priority", "unknown")) for t in tickets)
        content = "".join(bar(k, counts.get(k, 0), total, PRIORITY_COLORS[k]) for k in ("high", "medium", "low"))
        st.markdown(card(content or '<div class="siq-empty">No tickets</div>'), unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([1.6, 1], gap="medium")
    with left:
        section("Recent Tickets", "Latest records returned by the API")
        render_table(tickets, 8)
    with right:
        section("Operational Snapshot", "Real-time summary")
        statuses = Counter(str(t.get("status", "unknown")) for t in tickets)
        content = "".join(
            f'<div class="siq-statline"><span>{esc(nice(s))}</span><strong>{statuses.get(s, 0)}</strong></div>'
            for s in STATUSES
        )
        content += f'<div class="siq-statline"><span>AI-flagged tickets</span><strong>{flagged_count}</strong></div>'
        st.markdown(card(content), unsafe_allow_html=True)
        st.write("")
        st.markdown('<div class="siq-note">AI flag rate is not model accuracy. The model was trained on synthetic data; predictions need human oversight.</div>', unsafe_allow_html=True)


def ticket_management(tickets: list[dict], client: SupportIQClient) -> None:
    hero("Ticket Management", "Search, triage and inspect every support request", "SUPPORTIQ / OPERATIONS")
    search = st.text_input("Search tickets", placeholder="Search ticket ID or customer message…", key="ticket_search")
    a, b, c = st.columns(3)
    category = a.selectbox("Category", ("All",) + CATEGORIES, key="ticket_category")
    priority = b.selectbox("Priority", ("All",) + PRIORITIES, key="ticket_priority")
    status = c.selectbox("Status", ("All",) + STATUSES, key="ticket_status")
    q = search.strip().lower()
    filtered = [
        t for t in tickets
        if (not q or q in (str(t.get("ticket_id", "")) + " " + str(t.get("message", ""))).lower())
        and (category == "All" or t.get("category") == category)
        and (priority == "All" or t.get("priority") == priority)
        and (status == "All" or t.get("status") == status)
    ]
    section("Ticket Queue", f"{len(filtered)} matching of {len(tickets)} total")
    page_size = 10
    pages = max(1, math.ceil(len(filtered) / page_size))
    page = st.number_input("Page", min_value=1, max_value=pages, value=1, key="ticket_page")
    start = (page - 1) * page_size
    current = filtered[start:start + page_size]
    render_table(current)
    if not filtered:
        return
    st.write("")
    section("Inspect Ticket", "Select a ticket to view its AI decision")
    ids = [str(t.get("ticket_id")) for t in current]
    selected = st.selectbox("Ticket ID", ids, key="inspect_ticket")
    if selected:
        ticket = request(client.get_ticket, selected)
        if isinstance(ticket, dict):
            details(ticket)


def ai_intelligence(tickets: list[dict]) -> None:
    hero("AI Intelligence", "Model confidence, predictions and escalation visibility", "SUPPORTIQ / MODEL OPERATIONS")
    total = len(tickets)
    scores = [confidence_of(t) for t in tickets]
    avg = sum(scores) / len(scores) if scores else 0
    low = sum(score < .60 for score in scores)
    flagged_count = sum(flagged(t) for t in tickets)
    a, b, c, d = st.columns(4)
    with a: kpi("Average AI Score", f"{avg:.1%}", "Mean model score (simulated in Demo)", "✧")
    with b: kpi("Low-Score Tickets", str(low), "Below 60%", "!")
    with c: kpi("AI Flagged", str(flagged_count), "Escalation recommended", "◇")
    with d: kpi("Predictions", str(total), "Tickets in the current dataset", "▤")
    st.write("")
    left, right = st.columns(2)
    with left:
        section("Confidence Bands", "Distribution of prediction scores")
        bands = [
            ("Low (<60%)", sum(s < .60 for s in scores), "#FB7185"),
            ("Moderate (60–80%)", sum(.60 <= s < .80 for s in scores), "#F5B84D"),
            ("High (80–100%)", sum(s >= .80 for s in scores), "#34D399"),
        ]
        st.markdown(card("".join(bar(n, v, total, color) for n, v, color in bands)), unsafe_allow_html=True)
    with right:
        section("Original AI Predictions", "Category predictions at inference")
        prediction_counts = Counter(str(decision_of(t).get("category", "unknown")) for t in tickets)
        st.markdown(card(donut(prediction_counts, COLORS, total)), unsafe_allow_html=True)
    st.write("")
    st.markdown('<div class="siq-note">Important: Model scores are not calibrated probabilities of correctness. The existing classifier was evaluated on synthetic template-based data, so production reliability is unverified.</div>', unsafe_allow_html=True)
    st.write("")
    section("Prediction Inspector", "Examine individual AI decisions")
    if not tickets:
        st.info("No predictions yet.")
        return
    ids = [str(t.get("ticket_id")) for t in tickets]
    selected = st.selectbox("Choose ticket", ids, key="ai_inspector")
    ticket = next((t for t in tickets if str(t.get("ticket_id")) == selected), None)
    if ticket:
        details(ticket)


def human_review(tickets: list[dict], client: SupportIQClient) -> None:
    hero("Human Review Workspace", "Verify AI decisions and record accountable corrections", "SUPPORTIQ / HUMAN OVERSIGHT")
    pending = [t for t in tickets if t.get("status") == "pending_review"]
    a, b, c = st.columns(3)
    with a: kpi("Pending Reviews", str(len(pending)), "Tickets awaiting review", "◇")
    with b: kpi("AI-Flagged", str(sum(flagged(t) for t in tickets)), "Flagged by decision engine", "!")
    with c: kpi("High Priority Pending", str(sum(t.get("priority") == "high" for t in pending)), "Requires attention", "◷")
    st.write("")
    show_all = st.toggle("Include tickets outside the pending queue", value=False)
    available = tickets if show_all else pending
    if not available:
        st.success("There are no tickets in this review queue.")
        return
    selected = st.selectbox("Ticket to review", [str(t.get("ticket_id")) for t in available], key="review_selected")
    ticket = request(client.get_ticket, selected)
    if not isinstance(ticket, dict):
        return
    details(ticket)
    st.write("")
    section("Reviewer Decision", "Save a correction or confirm the AI recommendation")
    def index_or_zero(items: tuple, value: Any) -> int:
        return items.index(value) if value in items else 0
    with st.form(f"review_form_{selected}"):
        x, y, z = st.columns(3)
        category = x.selectbox("Final category", CATEGORIES, index=index_or_zero(CATEGORIES, ticket.get("category")))
        priority = y.selectbox("Final priority", PRIORITIES, index=index_or_zero(PRIORITIES, ticket.get("priority")))
        status = z.selectbox("Final status", ("open", "resolved"), index=1 if ticket.get("status") == "resolved" else 0)
        note = st.text_area("Review rationale", placeholder="Explain why the decision is accepted or corrected…", max_chars=1000)
        confirmed = st.checkbox("I have reviewed the ticket and verified this decision")
        submitted = st.form_submit_button("Save Reviewed Decision", type="primary", use_container_width=True)
    if submitted:
        if len(note.strip()) < 3:
            st.error("Please provide a review rationale of at least 3 characters.")
        elif not confirmed:
            st.error("Please confirm that you reviewed the ticket before saving.")
        else:
            result = request(
                client.review_ticket,
                ticket_id=selected,
                category=category,
                priority=priority,
                status=status,
                reviewer_note=note.strip(),
            )
            if result is not None:
                st.session_state["review_saved"] = selected
                st.rerun()
    if st.session_state.pop("review_saved", None) == selected:
        st.success("Human review saved successfully. The ticket and audit history have been updated.")


def audit_history(tickets: list[dict], client: SupportIQClient) -> None:
    hero("Audit & Review History", "Trace human decisions and review records", "SUPPORTIQ / AUDIT")
    if not tickets:
        st.info("No tickets available.")
        return
    selected = st.selectbox("Ticket", [str(t.get("ticket_id")) for t in tickets], key="audit_selected")
    result = request(client.get_reviews, selected)
    if result is None:
        return
    if isinstance(result, list):
        reviews = result
    elif isinstance(result, dict):
        reviews = result.get("reviews", [])
    else:
        reviews = []
    if not isinstance(reviews, list):
        reviews = []
    section("Review Timeline", f"{len(reviews)} recorded review(s)")
    if not reviews:
        st.markdown('<div class="siq-empty">No human review records for this ticket.</div>', unsafe_allow_html=True)
        return
    for index, review in enumerate(reviews, 1):
        if not isinstance(review, dict):
            continue
        timestamp = review.get("created_at", review.get("reviewed_at", "Timestamp unavailable"))
        review_id = review.get("id", index)
        with st.expander(f"Review {review_id} · {timestamp}", expanded=index == 1):
            fields = [
                ("Category", "previous_category", "new_category"),
                ("Priority", "previous_priority", "new_priority"),
                ("Status", "previous_status", "new_status"),
            ]
            lines = []
            for title, old_key, new_key in fields:
                before = review.get(old_key, "—")
                after = review.get(new_key, "—")
                lines.append(f'<div class="siq-statline"><span>{esc(title)}</span><strong>{esc(nice(before))} → {esc(nice(after))}</strong></div>')
            note = review.get("reviewer_note", review.get("note", "No note provided"))
            lines.append(f'<div class="siq-statline"><span>Reviewer note</span><strong>{esc(note)}</strong></div>')
            st.markdown(card("".join(lines)), unsafe_allow_html=True)
    st.caption("Audit entries come from the existing backend. Reviewer identity is not shown unless the API records it.")


def new_ticket(client: SupportIQClient) -> None:
    hero("Create Support Ticket", "Submit a customer message for AI-assisted classification", "SUPPORTIQ / INTAKE")
    left, right = st.columns([1.45, 1], gap="large")
    with left:
        section("New Request", "AI classification and routing")
        with st.form("new_ticket_form", clear_on_submit=False):
            message = st.text_area(
                "Customer message",
                height=220,
                max_chars=5000,
                placeholder="Example: I was charged twice for my subscription and need a refund.",
            )
            submitted = st.form_submit_button("Classify & Create Ticket", type="primary", use_container_width=True)
        if submitted:
            if len(message.strip()) < 5:
                st.error("Please enter at least 5 characters.")
            else:
                result = request(client.create_ticket, message.strip())
                if isinstance(result, dict) and result.get("ticket_id"):
                    st.session_state["last_created_ticket"] = str(result["ticket_id"])
                    st.success("Ticket successfully created and classified.")
                elif result is not None:
                    st.warning("The API returned an unexpected ticket creation response.")
    with right:
        section("Processing Workflow", "What happens next")
        steps = [
            ("01", "Validate", "FastAPI checks the submitted message."),
            ("02", "Predict", "The ML model classifies the ticket."),
            ("03", "Route", "Decision rules recommend priority and team."),
            ("04", "Review", "Uncertain or sensitive tickets are flagged."),
        ]
        content = "".join(
            f'<div class="siq-statline"><span><strong style="color:#74A9FF">{num}</strong> · {esc(title)}</span><span>{esc(desc)}</span></div>'
            for num, title, desc in steps
        )
        st.markdown(card(content), unsafe_allow_html=True)
    created_id = st.session_state.get("last_created_ticket")
    if created_id:
        st.write("")
        ticket = request(client.get_ticket, created_id)
        if isinstance(ticket, dict):
            details(ticket)


def main() -> None:
    with st.sidebar:
        st.markdown(
            '<div class="siq-brand"><div class="siq-logo">🧠</div>'
            '<div><div class="siq-brand-name">SupportIQ</div>'
            '<div class="siq-brand-sub">INTELLIGENCE OPERATIONS</div></div></div>',
            unsafe_allow_html=True,
        )
        st.caption("AI-assisted customer support")
        st.divider()
        mode = st.radio(
            "DATA SOURCE",
            ("Demo (sample data)", "Live (FastAPI)"),
            key="siq_mode",
            help="Demo is isolated in memory. Live reads your existing FastAPI database.",
        )
        st.divider()
        st.markdown('<div class="siq-eyebrow">WORKSPACE</div>', unsafe_allow_html=True)
        page = st.radio("Workspace", PAGES, label_visibility="collapsed", key="active_page")
        st.divider()
        if mode == "Demo (sample data)":
            st.caption("72 synthetic tickets · In-memory only")
            if st.button("↻ Reset demo data", use_container_width=True):
                for key in ("siq_demo_tickets", "siq_demo_reviews", "siq_demo_counter", "last_created_ticket", "review_saved"):
                    st.session_state.pop(key, None)
                st.rerun()
        else:
            st.caption("Live FastAPI · Your existing SQLite data")
            if st.button("↻ Refresh live data", use_container_width=True):
                st.rerun()
        st.caption("SupportIQ · Enterprise UI V1")
        st.caption("Portfolio demonstration · Human-in-the-loop")

    is_demo = mode == "Demo (sample data)"
    client = DemoClient() if is_demo else SupportIQClient()
    if is_demo:
        st.markdown(
            '<div class="siq-demo-banner"><strong>◆ DEMONSTRATION MODE</strong> — '
            'All 72 starting tickets, confidence scores, and outcomes are synthetic. '
            'New tickets and reviews are simulated in this browser session; '
            'no requests are sent to your FastAPI backend or SQLite database. '
            'Switch to <strong>Live (FastAPI)</strong> for real project records.</div>',
            unsafe_allow_html=True,
        )
    health = request(client.health)
    if health is None:
        st.warning("Live API is unavailable. Start FastAPI in another terminal, or select Demo mode.")
        st.stop()
    if not isinstance(health, dict):
        st.error("Unexpected health response.")
        st.stop()
    if health.get("status") != "healthy" or health.get("model_loaded") is False:
        st.error("Backend is responding but the application or model is not ready.")
        st.stop()

    if page == "New Ticket":
        new_ticket(client)
        return
    tickets = get_tickets(client)
    if tickets is None:
        st.stop()
    if page == "Command Center":
        overview(tickets)
    elif page == "Ticket Management":
        ticket_management(tickets, client)
    elif page == "AI Intelligence":
        ai_intelligence(tickets)
    elif page == "Human Review":
        human_review(tickets, client)
    elif page == "Audit History":
        audit_history(tickets, client)


if __name__ == "__main__":
    main()
