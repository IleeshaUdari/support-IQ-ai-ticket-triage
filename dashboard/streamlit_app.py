
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from dashboard.api_client import SupportIQClient, APIError


st.set_page_config(
    page_title="SupportIQ | Operations",
    page_icon="🧠",
    layout="wide",
)

st.markdown("""
<style>
.stApp {background:#F5F7FB;}
[data-testid="stSidebar"] {background:#101B35;}
[data-testid="stSidebar"] * {color:#F1F5F9;}
div[data-testid="stMetric"] {
    background:white;
    border:1px solid #E2E8F0;
    border-radius:14px;
    padding:16px;
}
h1,h2,h3 {letter-spacing:-0.025em;}
</style>
""", unsafe_allow_html=True)

client = SupportIQClient()

CATEGORIES = ["account", "billing", "delivery", "technical"]
PRIORITIES = ["low", "medium", "high"]
STATUSES = ["open", "pending_review", "resolved"]


def call_api(method, *args, **kwargs):
    try:
        return method(*args, **kwargs)
    except APIError as exc:
        st.error(str(exc))
        return None


def load_tickets():
    return call_api(client.get_all_tickets)


def label(value):
    return str(value).replace("_", " ").title()


def show_ticket(ticket):
    decision = ticket["decision"]

    st.subheader(ticket["ticket_id"])
    st.info(ticket["message"])

    a, b, c = st.columns(3)
    a.metric("Category", label(ticket["category"]))
    b.metric("Priority", label(ticket["priority"]))
    c.metric("Status", label(ticket["status"]))

    confidence = float(decision["confidence"])

    st.write("**AI Confidence:**", f"{confidence:.1%}")
    st.progress(max(0.0, min(1.0, confidence)))

    st.write("**Original AI category:**", decision["category"])
    st.write("**Assigned team:**", decision["assigned_team"])
    st.write(
        "**Human review flag:**",
        "Yes" if decision["needs_human_review"] else "No",
    )
    st.write("**Decision reason:**", decision["reason"])
    st.caption(f"Model version: {decision['model_version']}")

    if ticket["category"] != decision["category"]:
        st.warning("The category was corrected by a reviewer.")


def show_distribution(tickets, key, title):
    st.subheader(title)

    counts = Counter(ticket[key] for ticket in tickets)
    total = max(len(tickets), 1)

    for name, count in counts.most_common():
        st.write(f"**{label(name)}** — {count}")
        st.progress(count / total)


def overview(tickets):
    st.title("Operations Overview")
    st.caption("AI-assisted customer support monitoring")

    total = len(tickets)
    pending = sum(
        t["status"] == "pending_review" for t in tickets
    )
    high = sum(t["priority"] == "high" for t in tickets)
    resolved = sum(t["status"] == "resolved" for t in tickets)
    flagged = sum(
        bool(t["decision"]["needs_human_review"])
        for t in tickets
    )

    cols = st.columns(5)
    cols[0].metric("Total Tickets", total)
    cols[1].metric("Pending Review", pending)
    cols[2].metric("High Priority", high)
    cols[3].metric("Resolved", resolved)
    cols[4].metric(
        "AI Flag Rate",
        f"{flagged / total:.1%}" if total else "0%",
    )

    if not tickets:
        st.info("No tickets yet. Create your first ticket.")
        return

    st.divider()
    left, right = st.columns(2)

    with left:
        show_distribution(
            tickets, "category", "Category Distribution"
        )

    with right:
        show_distribution(
            tickets, "priority", "Priority Distribution"
        )

    st.subheader("Recent Tickets")

    for ticket in tickets[:10]:
        with st.expander(
            f"{ticket['ticket_id']} | "
            f"{label(ticket['category'])} | "
            f"{label(ticket['status'])}"
        ):
            show_ticket(ticket)


def ticket_queue(tickets):
    st.title("Ticket Management")
    st.caption("Search, filter and inspect tickets")

    search = st.text_input(
        "Search by ticket ID or message"
    ).strip().lower()

    a, b, c = st.columns(3)

    category = a.selectbox(
        "Category", ["All"] + CATEGORIES
    )
    priority = b.selectbox(
        "Priority", ["All"] + PRIORITIES
    )
    status = c.selectbox(
        "Status", ["All"] + STATUSES
    )

    filtered = []

    for ticket in tickets:
        searchable = (
            ticket["ticket_id"] + " " + ticket["message"]
        ).lower()

        if search and search not in searchable:
            continue
        if category != "All" and ticket["category"] != category:
            continue
        if priority != "All" and ticket["priority"] != priority:
            continue
        if status != "All" and ticket["status"] != status:
            continue

        filtered.append(ticket)

    st.write(f"**{len(filtered)} matching tickets**")

    if not filtered:
        st.info("No tickets match the selected filters.")
        return

    page_size = 10
    pages = max(1, (len(filtered) + page_size - 1) // page_size)

    page = st.number_input(
        "Page", min_value=1, max_value=pages, value=1
    )

    start = (page - 1) * page_size

    for ticket in filtered[start:start + page_size]:
        with st.expander(
            f"{ticket['ticket_id']} | "
            f"{label(ticket['category'])} | "
            f"{label(ticket['priority'])} | "
            f"{label(ticket['status'])}"
        ):
            show_ticket(ticket)


def ai_insights(tickets):
    st.title("AI Insights")

    if not tickets:
        st.info("No predictions available.")
        return

    scores = [
        float(t["decision"]["confidence"])
        for t in tickets
    ]

    flagged = sum(
        bool(t["decision"]["needs_human_review"])
        for t in tickets
    )

    a, b, c = st.columns(3)

    a.metric("Average Model Score", f"{sum(scores)/len(scores):.1%}")
    b.metric("Low-Score Tickets", sum(s < 0.60 for s in scores))
    c.metric("AI-Flagged Tickets", flagged)

    st.divider()
    st.subheader("Confidence Distribution")

    bands = {
        "Low (<60%)": sum(s < 0.60 for s in scores),
        "Moderate (60–80%)": sum(
            0.60 <= s < 0.80 for s in scores
        ),
        "High (80–100%)": sum(s >= 0.80 for s in scores),
    }

    for name, count in bands.items():
        st.write(f"**{name}:** {count}")
        st.progress(count / len(scores))

    st.subheader("Individual Predictions")

    for ticket in tickets[:50]:
        decision = ticket["decision"]

        with st.expander(
            f"{ticket['ticket_id']} — "
            f"{float(decision['confidence']):.1%}"
        ):
            show_ticket(ticket)

    st.warning(
        "Model probabilities are not calibrated reliability "
        "estimates. The training dataset is synthetic."
    )


def human_review(tickets):
    st.title("Human Review Workspace")

    pending = [
        t for t in tickets
        if t["status"] == "pending_review"
    ]

    st.metric("Awaiting Review", len(pending))

    include_all = st.checkbox(
        "Include tickets outside the pending queue"
    )

    available = tickets if include_all else pending

    if not available:
        st.success("No tickets in this review queue.")
        return

    ids = [t["ticket_id"] for t in available]

    selected = st.selectbox("Select ticket", ids)

    ticket = call_api(client.get_ticket, selected)

    if ticket is None:
        return

    show_ticket(ticket)
    st.divider()

    with st.form(f"review_{selected}"):
        category = st.selectbox(
            "Correct category",
            CATEGORIES,
            index=CATEGORIES.index(ticket["category"]),
        )

        priority = st.selectbox(
            "Correct priority",
            PRIORITIES,
            index=PRIORITIES.index(ticket["priority"]),
        )

        status = st.selectbox(
            "New status",
            ["open", "resolved"],
        )

        note = st.text_area(
            "Reviewer note",
            max_chars=1000,
        )

        submitted = st.form_submit_button(
            "Save Human Review",
            type="primary",
        )

    if submitted:
        if len(note.strip()) < 3:
            st.error("Reviewer note must contain at least 3 characters.")
        else:
            result = call_api(
                client.review_ticket,
                ticket_id=selected,
                category=category,
                priority=priority,
                status=status,
                reviewer_note=note.strip(),
            )

            if result is not None:
                st.success("Review saved successfully.")
                st.rerun()


def review_history(tickets):
    st.title("Review History")

    if not tickets:
        st.info("No tickets available.")
        return

    ids = [t["ticket_id"] for t in tickets]

    selected = st.selectbox("Select ticket", ids)

    result = call_api(client.get_reviews, selected)

    if result is None:
        return

    reviews = result.get("reviews", [])

    st.metric("Recorded Reviews", len(reviews))

    if not reviews:
        st.info("No human reviews for this ticket.")
        return

    for review in reviews:
        with st.expander(
            f"Review #{review['id']} | "
            f"{review['created_at']}"
        ):
            st.write(
                "**Category:**",
                review["previous_category"],
                "→",
                review["new_category"],
            )
            st.write(
                "**Priority:**",
                review["previous_priority"],
                "→",
                review["new_priority"],
            )
            st.write(
                "**Status:**",
                review["previous_status"],
                "→",
                review["new_status"],
            )
            st.write(
                "**Reviewer note:**",
                review["reviewer_note"],
            )


def create_ticket():
    st.title("New Support Ticket")

    with st.form("create_ticket"):
        message = st.text_area(
            "Customer message",
            height=150,
            max_chars=5000,
        )

        submitted = st.form_submit_button(
            "Classify and Create",
            type="primary",
        )

    if submitted:
        if len(message.strip()) < 5:
            st.error("Message must contain at least 5 characters.")
        else:
            result = call_api(
                client.create_ticket,
                message.strip(),
            )

            if result is not None:
                st.session_state["created_ticket_id"] = (
                    result["ticket_id"]
                )
                st.success("Ticket created.")

    ticket_id = st.session_state.get("created_ticket_id")

    if ticket_id:
        ticket = call_api(client.get_ticket, ticket_id)

        if ticket is not None:
            show_ticket(ticket)


with st.sidebar:
    st.title("🧠 SupportIQ")
    st.caption("AI Operations Center")
    st.divider()

    page = st.radio(
        "Workspace",
        [
            "Overview",
            "Ticket Queue",
            "AI Insights",
            "Human Review",
            "Review History",
            "New Ticket",
        ],
    )

    st.divider()

    if st.button("Refresh Data", use_container_width=True):
        st.rerun()

    st.caption("SupportIQ | Portfolio MVP")


health = call_api(client.health)

if health is None:
    st.stop()

if (
    health.get("status") != "healthy"
    or not health.get("model_loaded")
):
    st.error("FastAPI or the AI model is not ready.")
    st.stop()

if page == "New Ticket":
    create_ticket()
else:
    tickets = load_tickets()

    if tickets is None:
        st.stop()

    if page == "Overview":
        overview(tickets)
    elif page == "Ticket Queue":
        ticket_queue(tickets)
    elif page == "AI Insights":
        ai_insights(tickets)
    elif page == "Human Review":
        human_review(tickets)
    elif page == "Review History":
        review_history(tickets)
