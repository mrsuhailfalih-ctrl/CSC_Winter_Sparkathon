from __future__ import annotations

import streamlit as st

from utils.serper_search import search_with_serper, serper_is_configured

st.set_page_config(page_title="Hackathon Finder", page_icon="🔎", layout="wide")
st.title("🔎 Hackathon Finder")
st.write("Search the web for hackathons using Serper's Google Search API.")
st.caption("Search results are displayed directly from Serper without post-search topic, date, event-type, or domain filtering. Verify details on the source pages.")

left, right = st.columns(2)
with left:
    interests = st.text_input("Interests / technologies", placeholder="AI, Python, climate, social good")
    details = st.text_area("Other preferences", placeholder="Online, free, beginner-friendly", height=100)
with right:
    start_date = st.date_input("Earliest event date", key="period_start")
    end_date = st.date_input("Latest event date", key="period_end")

if not serper_is_configured():
    st.warning("Serper search is not configured. Set SERPER_API_KEY in your environment or Streamlit secrets to enable search.")

if st.button("Find hackathons", type="primary", use_container_width=True):
    if not interests.strip() and not details.strip():
        st.warning("Enter at least one interest or preference.")
    elif start_date > end_date:
        st.error("The earliest date must be on or before the latest date.")
    else:
        with st.spinner("Searching the web with Serper..."):
            st.session_state["serper_search_result"] = search_with_serper(
                interests, details, start_date, end_date
            )

result = st.session_state.get("serper_search_result")
if result:
    if result.get("error"):
        st.error(result["error"])
    else:
        events = result.get("results", [])
        st.caption(f'Search query: {result.get("query", "")}. Results are unfiltered Serper organic results.')
        if events:
            st.success(f"Serper returned {len(events)} search result(s).")
            for index, item in enumerate(events, start=1):
                if not isinstance(item, dict):
                    continue
                title = item.get("title") or "Untitled result"
                link = item.get("link")
                with st.container(border=True):
                    st.markdown(f"### {index}. {title}")
                    if item.get("date"):
                        st.caption(str(item["date"]))
                    if item.get("snippet"):
                        st.write(item["snippet"])
                    if link:
                        st.link_button("Open search result", str(link))
                    elif item.get("displayLink"):
                        st.write(item["displayLink"])
        else:
            st.info("Serper returned no organic search results for this query.")

st.divider()
st.caption("Keep your Serper API key private. Search terms are sent to Serper to perform the web search.")
