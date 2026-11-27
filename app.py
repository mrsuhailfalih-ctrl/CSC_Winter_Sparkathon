from __future__ import annotations

import streamlit as st

from utils.live_search import get_official_sources

st.set_page_config(page_title="Hackathon Finder", page_icon="🔎", layout="wide")
st.title("🔎 Hackathon Finder")
st.write("Browse hackathons directly on event-hosting platforms—no general web search or aggregator results.")
st.info(
    "This app links to official platform listings; it does not scrape or claim to search their databases. "
    "The platforms do not share a common public event-search API. Open a source, search within it, "
    "and verify event dates, organizer, registration, and age rules on the event page."
)

left, right = st.columns(2)
with left:
    interests = st.text_input("Interests / technologies", placeholder="AI, Python, climate, social good")
    details = st.text_area("Other preferences", placeholder="Online, free, beginner-friendly", height=100)
with right:
    start_date = st.date_input("Earliest event date", key="period_start")
    end_date = st.date_input("Latest event date", key="period_end")

if st.button("Show official event platforms", type="primary", use_container_width=True):
    if not interests.strip() and not details.strip():
        st.warning("Enter at least one interest or preference to prepare your search phrase.")
    elif start_date > end_date:
        st.error("The start date must be on or before the latest date.")
    else:
        st.session_state["official_sources"] = get_official_sources(interests, details, start_date, end_date)
        st.session_state["official_phrase"] = st.session_state["official_sources"][0]["search_phrase"]

sources = st.session_state.get("official_sources")
if sources:
    st.subheader("Search phrase to use on each platform")
    st.code(st.session_state["official_phrase"], language=None)
    st.caption("Use the platform's own search and date filters if available. The app does not receive or rank results from these sites.")
    for source in sources:
        with st.container(border=True):
            st.markdown(f"### {source['name']}")
            st.write(source["note"])
            st.link_button(f"Open {source['name']}", source["url"])

st.divider()
st.caption("Search results and eligibility rules can change. For minors, have a parent or guardian review event terms and registration requirements.")
