from __future__ import annotations

import streamlit as st

from utils.live_search import search_official_events

st.set_page_config(page_title="Hackathon Finder", page_icon="🔎", layout="wide")
st.title("🔎 Hackathon Finder")
st.write("Find hackathons from public event pages on official hosting platforms.")
st.caption("No DuckDuckGo or general-web results. Listings are best-effort and must be confirmed on the organizer's page.")
st.info(
    "The finder checks public pages on Devpost, Devfolio, MLH, Unstop, Eventbrite, and Luma. "
    "It extracts events when a platform page exposes structured event details. Some sites render listings with JavaScript or limit automated access, so results may be incomplete."
)

left, right = st.columns(2)
with left:
    interests = st.text_input("Interests / technologies", placeholder="AI, Python, climate, social good")
    details = st.text_area("Other preferences (used to match text)", placeholder="Online, free, beginner-friendly", height=100)
with right:
    start_date = st.date_input("Earliest event date", key="period_start")
    end_date = st.date_input("Latest event date", key="period_end")

if st.button("Find hackathons", type="primary", use_container_width=True):
    if not interests.strip() and not details.strip():
        st.warning("Enter at least one interest or preference.")
    elif start_date > end_date:
        st.error("The start date must be on or before the latest date.")
    else:
        with st.spinner("Checking official event platforms for public structured listings..."):
            # Cache successful/empty search briefly to reduce repeat requests.
            @st.cache_data(ttl=900, show_spinner=False)
            def cached_search(topic: str, preferences: str, start, end):
                return search_official_events(topic, preferences, start, end)
            st.session_state["official_event_results"] = cached_search(interests, details, start_date, end_date)

result = st.session_state.get("official_event_results")
if result:
    st.caption(result["message"])
    events = result["results"]
    if events:
        st.success(f"Found {len(events)} possible event(s) from official-platform pages.")
        for event in events:
            with st.container(border=True):
                st.markdown(f"### {event['name']}")
                st.caption(f"Source platform: {event['source_platform']}")
                if event["start_date"]:
                    date_text = event["start_date"].isoformat()
                    if event["end_date"] and event["end_date"] != event["start_date"]:
                        date_text += f" – {event['end_date'].isoformat()}"
                    st.write(f"**Event dates:** {date_text} (structured date found; verify on organizer page)")
                else:
                    st.warning("No structured start date found. Verify whether this event is in your date range.")
                if event["location"]:
                    st.write(f"**Location:** {event['location']}")
                if event["snippet"]:
                    st.write(event["snippet"])
                st.link_button("Open official platform event page", event["url"])
    else:
        st.warning("No matching structured event listings were found on the checked pages. This does not prove there are no events: some platforms render listings dynamically or limit automated access.")
    with st.expander("Source diagnostics"):
        st.json(result["diagnostics"])

st.divider()
st.caption("For minors, ask a parent or guardian to review registration, age limits, and platform terms before signing up.")
