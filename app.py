from __future__ import annotations

import streamlit as st

from utils.live_search import search_official_events
from utils.momen_ai import momen_is_configured, rank_events_with_momen

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

momen_enabled = momen_is_configured()
use_momen = st.checkbox(
    "Use Momen AI to rank discovered events",
    value=False,
    disabled=not momen_enabled,
    help="Optional. Momen receives candidate event titles, descriptions, dates, URLs, and your preferences for ranking. It does not discover or verify events.",
)
if not momen_enabled:
    st.caption("Momen AI is optional and not configured on this server yet. The app works without it.")

if st.button("Find hackathons", type="primary", use_container_width=True):
    if not interests.strip() and not details.strip():
        st.warning("Enter at least one interest or preference.")
    elif start_date > end_date:
        st.error("The start date must be on or before the latest date.")
    else:
        with st.spinner("Checking official event platforms for public structured listings..."):
            @st.cache_data(ttl=900, show_spinner=False)
            def cached_search(topic: str, preferences: str, start, end):
                return search_official_events(topic, preferences, start, end)
            result = cached_search(interests, details, start_date, end_date)
            events = result["results"]
            if use_momen and events:
                with st.spinner("Asking Momen AI to rank the discovered candidates..."):
                    ai_result = rank_events_with_momen(events)
                result["momen_ai_available"] = ai_result["available"]
                result["momen_ai_message"] = ai_result["message"]
                for event in events:
                    ranking = ai_result["rankings"].get(event["url"])
                    if ranking:
                        event["ai_score"] = ranking["score"]
                        event["ai_reason"] = ranking["reason"]
                if ai_result["available"]:
                    events.sort(key=lambda event: event.get("ai_score", -1), reverse=True)
            st.session_state["official_event_results"] = result

result = st.session_state.get("official_event_results")
if result:
    st.caption(result["message"])
    if result.get("momen_ai_message"):
        st.info(result["momen_ai_message"])
    events = result["results"]
    if events:
        st.success(f"Found {len(events)} possible event(s) from official-platform pages.")
        for event in events:
            with st.container(border=True):
                st.markdown(f"### {event['name']}")
                st.caption(f"Source platform: {event['source_platform']}")
                if "ai_score" in event:
                    st.caption(f"Momen AI relevance: {event['ai_score']}/100 — {event.get('ai_reason', '')}")
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
st.caption("For minors, ask a parent or guardian to review registration, age limits, platform terms, and AI data sharing before signing up.")
