from __future__ import annotations

import streamlit as st

from utils.search_filter import filter_search_results
from utils.serper_search import search_with_serper, serper_is_configured

st.set_page_config(page_title="Hackathon Finder", page_icon="🔎", layout="wide")
st.title("🔎 Hackathon Finder")
st.write("Search the web for hackathons using Serper's Google Search API.")
st.caption("Broad hackathon directories and roundup pages are hidden. Search result dates can be stale or refer to publication dates, so confirm event dates and deadlines with organizers.")

left, right = st.columns(2)
with left:
    interests = st.text_input("Interests / technologies", placeholder="AI, Python, climate, social good")
    details = st.text_area("Other preferences", placeholder="Free, beginner-friendly", height=100)
    age = st.number_input("Your age", min_value=5, max_value=100, value=18, step=1, help="Used to search for events that may fit your age. Always confirm eligibility with the organizer.")
with right:
    start_date = st.date_input("Earliest event date", key="period_start")
    end_date = st.date_input("Latest event date", key="period_end")
    event_format = st.selectbox("Hackathon format", ("Any", "Online", "In-person"), index=0)
    location = st.text_input(
        "Location / vicinity",
        placeholder="City, state/province, or country",
        help="Add a location for in-person events, or optionally narrow an Any search. Leave blank for online events or a worldwide search.",
    )

if not serper_is_configured():
    st.warning("Serper search is not configured. Set SERPER_API_KEY in your environment or Streamlit secrets to enable search.")

if st.button("Find hackathons", type="primary", use_container_width=True):
    if not interests.strip() and not details.strip():
        st.warning("Enter at least one interest or preference.")
    elif start_date > end_date:
        st.error("The earliest date must be on or before the latest date.")
    elif event_format == "In-person" and not location.strip():
        st.warning("Enter a city, state/province, or country for in-person events.")
    else:
        with st.spinner("Searching the web with Serper..."):
            st.session_state["serper_search_result"] = search_with_serper(
                interests,
                details,
                start_date,
                end_date,
                age=int(age),
                event_format=event_format,
                location=location,
            )

result = st.session_state.get("serper_search_result")
if result:
    if result.get("error"):
        st.error(result["error"])
    else:
        raw_results = result.get("results", [])
        events = filter_search_results(raw_results)
        hidden_count = len(raw_results) - len(events)
        st.caption(f'Search query: {result.get("query", "")}.')
        st.info("Dates shown in search snippets are not verified event dates. Check the organizer's page for the current schedule, deadline, and eligibility.")
        if events:
            st.success(f"Showing {len(events)} result(s).")
            if hidden_count:
                st.caption(f"Filtered out {hidden_count} broad directory or roundup result(s).")
            for index, item in enumerate(events, start=1):
                title = item.get("title") or "Untitled result"
                link = item.get("link")
                with st.container(border=True):
                    st.markdown(f"### {index}. {title}")
                    # Serper's `date` is usually the indexed/published date, not the event schedule.
                    if item.get("snippet"):
                        st.write(item["snippet"])
                    if link:
                        st.link_button("Open event/source page and verify dates", str(link))
                    elif item.get("displayLink"):
                        st.write(item["displayLink"])
        elif raw_results:
            st.info("Serper returned results, but they all looked like broad hackathon directories or roundups. Try a more specific query such as an event topic, age group, or location.")
        else:
            st.info("Serper returned no organic search results for this query.")

st.divider()
st.caption("Keep your Serper API key private. Search terms and the age/location/format preferences you enter are sent to Serper to perform the web search. Eligibility and event schedules are not independently verified.")
