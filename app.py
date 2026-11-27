from __future__ import annotations

import streamlit as st

from utils.live_search import search_official_events
from utils.momen_ai import momen_is_configured, search_events_with_momen

st.set_page_config(page_title="Hackathon Finder", page_icon="🔎", layout="wide")
st.title("🔎 Hackathon Finder")
st.write("Find hackathons from public event pages on official hosting platforms.")
st.caption("No DuckDuckGo or general-web results. Event pages are checked on their source platform; verify details with organizers.")
st.info(
    "When configured, Momen AI can search the web for event URLs on Devpost, Devfolio, MLH, Unstop, Eventbrite, and Luma. "
    "The app then fetches candidate pages from those platforms and only displays pages with corroborating event metadata."
)

left, right = st.columns(2)
with left:
    interests = st.text_input("Interests / technologies", placeholder="AI, Python, climate, social good")
    details = st.text_area("Other preferences (used in the search request)", placeholder="Online, free, beginner-friendly", height=100)
with right:
    start_date = st.date_input("Earliest event date", key="period_start")
    end_date = st.date_input("Latest event date", key="period_end")

momen_enabled = momen_is_configured()
use_momen = st.checkbox(
    "Use Momen AI web search for events",
    value=momen_enabled,
    disabled=not momen_enabled,
    help="Momen receives the interests, preferences, and date range you entered. It must have a web-search/browsing tool enabled in the Momen project. Results are restricted to allowlisted event-platform URLs and page-fetched before display.",
)
if not momen_enabled:
    st.caption("Momen search is not configured on this server. The app will check public platform listings directly instead.")

if st.button("Find hackathons", type="primary", use_container_width=True):
    if not interests.strip() and not details.strip():
        st.warning("Enter at least one interest or preference.")
    elif start_date > end_date:
        st.error("The start date must be on or before the latest date.")
    else:
        with st.spinner("Searching for hackathon events..."):
            if use_momen:
                result = search_events_with_momen(interests, details, start_date, end_date)
                if result.get("error"):
                    st.warning(result["error"])
                    st.caption("Using official-platform page discovery as a fallback.")
                    fallback = search_official_events(interests, details, start_date, end_date)
                    result = {**fallback, "search_mode": "official_platform_fallback", "momen_error": result["error"]}
                else:
                    result["search_mode"] = "momen_web_search"
            else:
                result = search_official_events(interests, details, start_date, end_date)
                result["search_mode"] = "official_platform_pages"
            st.session_state["official_event_results"] = result

result = st.session_state.get("official_event_results")
if result:
    st.caption(result.get("message", "Results are best-effort; verify on organizer pages."))
    events = result.get("results", [])
    if events:
        st.success(f"Found {len(events)} possible event(s) from official-platform pages.")
        for event in events:
            with st.container(border=True):
                st.markdown(f"### {event['name']}")
                st.caption(f"Source platform: {event['source_platform']}")
                if event.get("start_date"):
                    date_text = event["start_date"].isoformat()
                    if event.get("end_date") and event["end_date"] != event["start_date"]:
                        date_text += f" – {event['end_date'].isoformat()}"
                    st.write(f"**Event dates:** {date_text} (verify on organizer page)")
                else:
                    st.warning("No date could be confirmed from page metadata. Check whether this event fits your date range.")
                if event.get("location"):
                    st.write(f"**Location:** {event['location']}")
                if event.get("snippet"):
                    st.write(event["snippet"])
                st.link_button("Open official platform event page", event["url"])
    else:
        st.warning("No matching verifiable events were found. Some platforms block automated access or render listings dynamically; try again or browse the platform directly.")
    with st.expander("Source diagnostics"):
        st.json(result.get("diagnostics", {}))

st.divider()
st.caption("For minors, ask a parent or guardian to review registration, age limits, platform terms, and what search information is sent to Momen before enabling AI search.")
