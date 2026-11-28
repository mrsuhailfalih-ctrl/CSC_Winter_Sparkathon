from __future__ import annotations

import streamlit as st

from utils.search_filter import filter_search_results
from utils.serper_search import search_with_serper, serper_is_configured

st.set_page_config(page_title="Hackathon Finder", page_icon="🔎", layout="wide")
st.title("🔎 Hackathon Finder")
st.write("Search the web for hackathons using Serper's Google Search API.")
st.caption("With a date range selected, results without clear event schedule dates are hidden. Search snippets are still not authoritative; confirm schedules and eligibility with organizers.")

left, right = st.columns(2)
with left:
    interests = st.text_input("Interests / technologies", placeholder="AI, Python, climate, social good")
    details = st.text_area("Other preferences", placeholder="Free, beginner-friendly", height=100)
    age = st.number_input("Your age", min_value=5, max_value=100, value=18, step=1, help="Used to search for events that may fit your age. Confirm eligibility with organizers.")
with right:
    start_date = st.date_input("Earliest event date", key="period_start")
    end_date = st.date_input("Latest event date", key="period_end")
    event_format = st.selectbox("Hackathon format", ("Any", "Online", "In-person"), index=0)
    location = st.text_input("Location / vicinity", placeholder="City, state/province, or country")

if not serper_is_configured():
    st.warning("Serper search is not configured. Set SERPER_API_KEY in your environment or Streamlit secrets to enable search.")

if st.button("Find hackathons", type="primary", use_container_width=True):
    if not interests.strip() and not details.strip():
        st.warning("Enter at least one interest or preference.")
    elif start_date > end_date:
        st.error("The earliest date must be on or before the latest date.")
    elif event_format == "In-person" and not location.strip():
        st.warning("Enter a location for in-person events.")
    else:
        with st.spinner("Searching the web with Serper..."):
            st.session_state["serper_search_result"] = search_with_serper(
                interests, details, start_date, end_date,
                age=int(age), event_format=event_format, location=location,
            )

result = st.session_state.get("serper_search_result")
if result:
    if result.get("error"):
        st.error(result["error"])
    else:
        raw_results = result.get("results", [])
        events = filter_search_results(raw_results, start_date, end_date)
        removed = len(raw_results) - len(events)
        st.caption(f'Search query: {result.get("query", "")}.')
        st.info("Only results with event-related, year-specific dates in the selected window are shown. Dates are inferred from search snippets, not independently verified. Open the source page before relying on them.")
        if events:
            st.success(f"Showing {len(events)} result(s) matching the date range.")
            if removed:
                st.caption(f"Omitted {removed} results because they were broad listings, lacked clear event dates, or had dates outside the selected range.")
            for index, item in enumerate(events, start=1):
                with st.container(border=True):
                    st.markdown(f"### {index}. {item.get('title') or 'Untitled result'}")
                    dates = item.get("date_verification", {}).get("dates", [])
                    if dates:
                        st.caption("Date evidence: " + ", ".join(dates) + " (verify with organizer)")
                    if item.get("snippet"):
                        st.write(item["snippet"])
                    if item.get("link"):
                        st.link_button("Open source page and verify dates", str(item["link"]))
        elif raw_results:
            st.info("No results had clear event-date evidence inside the selected range. Try adjusting the dates or use a more specific query. No search-result publication dates were treated as event dates.")
        else:
            st.info("Serper returned no organic search results for this query.")

st.divider()
st.caption("Keep your Serper API key private. Search terms and age/location/format preferences are sent to Serper. Event schedules and eligibility are not independently verified.")
