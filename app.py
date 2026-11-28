from __future__ import annotations

from datetime import date

import streamlit as st

from utils.serper_search import search_hackathons

st.set_page_config(page_title="Hackathon Finder", page_icon="🔎", layout="wide")
st.title("🔎 Hackathon Finder")
st.write("Find hackathons using live Serper web search. Review each organizer page for current dates and eligibility.")
st.caption("Search snippets can be incomplete or stale. Unknown dates, age limits, and event formats are shown as unverified rather than treated as confirmed.")

left, right = st.columns(2)
with left:
    interests = st.text_input("Interests / technologies", placeholder="AI, Python, climate, social good")
    details = st.text_area("Other preferences", placeholder="Free, beginner-friendly, student-focused", height=90)
    age = st.number_input("Your age", min_value=5, max_value=99, value=14, step=1)
with right:
    event_format = st.radio(
        "Preferred event format",
        options=("Any", "Online", "In-person"),
        horizontal=True,
        help="Events without clear format information may still be included; verify the organizer page.",
    )
    start_date = st.date_input("Earliest event date", value=date.today(), key="period_start")
    end_date = st.date_input("Latest event date", key="period_end")

if st.button("Find hackathons", type="primary", use_container_width=True):
    if not interests.strip() and not details.strip():
        st.warning("Enter at least one interest or preference.")
    elif start_date > end_date:
        st.error("The start date must be on or before the latest date.")
    else:
        with st.spinner("Searching the web for hackathons..."):
            result = search_hackathons(
                interests=interests,
                details=details,
                start=start_date,
                end=end_date,
                age=int(age),
                event_format=event_format,
            )
            st.session_state["serper_event_results"] = result

result = st.session_state.get("serper_event_results")
if result:
    if result.get("error"):
        st.error(result["error"])
    else:
        st.caption(result.get("message", "Search results are best-effort; verify details with organizers."))
        events = result.get("results", [])
        if events:
            st.success(f"Found {len(events)} possible hackathon(s).")
            for event in events:
                with st.container(border=True):
                    st.markdown(f"### {event['name']}")
                    st.write(f"**Age check:** {event.get('age_status', 'Not confirmed — check official rules')}")
                    st.write(f"**Format:** {event.get('format_status', 'Not confirmed — check official page')}")
                    if event.get("date_match"):
                        st.write(f"**Date check:** {event['date_match']}")
                    if event.get("snippet"):
                        st.write(event["snippet"])
                    st.link_button("Open event / organizer page", event["url"])
        else:
            st.warning("No likely matches were returned. Try broader interests or a wider date range.")
        with st.expander("Search diagnostics"):
            st.json(result.get("diagnostics", {}))

st.divider()
st.caption("For minors, ask a parent or guardian to review age limits, parental-consent rules, registration requirements, and organizer terms. The app does not determine legal eligibility.")
