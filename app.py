from __future__ import annotations

import streamlit as st

from utils.luna_search import luna_is_configured, search_with_luna
from utils.search_filter import filter_search_results
from utils.serper_search import search_with_serper, serper_is_configured

st.set_page_config(page_title="Hackathon Finder", page_icon="🔎", layout="wide")
st.title("🔎 Hackathon Finder")
st.write("Find hackathons using AI web search, with Serper as a fallback.")
st.caption("The model's web-search tool must be enabled by its API provider. Event dates and eligibility are not guaranteed; verify on organizer pages.")

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

if not serper_is_configured() and not luna_is_configured():
    st.warning("Configure SERPER_API_KEY or LUNA_API_KEY in environment variables / Streamlit secrets to enable search.")
elif luna_is_configured():
    st.caption("GPT web search is configured. If unavailable, the app will try Serper when configured.")

if st.button("Find hackathons", type="primary", use_container_width=True):
    if not interests.strip() and not details.strip():
        st.warning("Enter at least one interest or preference.")
    elif start_date > end_date:
        st.error("The earliest date must be on or before the latest date.")
    elif event_format == "In-person" and not location.strip():
        st.warning("Enter a location for in-person events.")
    else:
        args = dict(
            age=int(age), event_format=event_format, location=location,
        )
        with st.spinner("Searching the web for hackathons..."):
            if luna_is_configured():
                result = search_with_luna(interests, details, start_date, end_date, **args)
                if result.get("error") and serper_is_configured():
                    st.warning(result["error"] + " Falling back to Serper search.")
                    result = search_with_serper(interests, details, start_date, end_date, **args)
                    result["search_provider"] = "Serper fallback"
                else:
                    result["search_provider"] = "GPT web search"
            elif serper_is_configured():
                result = search_with_serper(interests, details, start_date, end_date, **args)
                result["search_provider"] = "Serper"
            else:
                result = {"results": [], "error": "No search provider is configured."}
            st.session_state["search_result"] = result

result = st.session_state.get("search_result")
if result:
    if result.get("error"):
        st.error(result["error"])
    else:
        raw_results = result.get("results", [])
        events = filter_search_results(raw_results, start_date, end_date)
        removed = len(raw_results) - len(events)
        st.caption(f"Search provider: {result.get('search_provider', 'Search')}. Query: {result.get('query', '')}")
        st.info("Known event dates outside the selected range are hidden. Results without reliable dates remain visible as unverified so the filter does not discard potentially relevant events.")
        if events:
            st.success(f"Showing {len(events)} result(s).")
            if removed:
                st.caption(f"Filtered out {removed} obvious directory/roundup or confirmed out-of-range result(s).")
            for index, item in enumerate(events, start=1):
                with st.container(border=True):
                    st.markdown(f"### {index}. {item.get('title') or 'Untitled result'}")
                    verify = item.get("date_verification", {})
                    if verify.get("dates"):
                        st.caption("Date evidence: " + ", ".join(verify["dates"]) + " — confirm with organizer.")
                    else:
                        st.warning("Event dates could not be verified against the selected range.")
                    if item.get("event_start_date") or item.get("event_end_date"):
                        st.write(f"**Event schedule:** {item.get('event_start_date') or 'Unknown'} – {item.get('event_end_date') or item.get('event_start_date') or 'Unknown'}")
                    if item.get("format"):
                        st.write(f"**Format:** {item['format']}")
                    if item.get("location"):
                        st.write(f"**Location:** {item['location']}")
                    if item.get("age_eligibility"):
                        st.write(f"**Age eligibility:** {item['age_eligibility']}")
                    if item.get("snippet"):
                        st.write(item["snippet"])
                    if item.get("link"):
                        st.link_button("Open source page and verify", str(item["link"]))
        elif raw_results:
            st.info("No results were returned after removing broad roundups and events confirmed to be outside the selected range.")
        else:
            st.info("The search provider returned no event results.")

st.divider()
st.caption("Keep API keys private. Search preferences are sent to the configured AI/search provider. Verify dates, age eligibility, and event details with organizers.")
