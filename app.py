import hashlib

import streamlit as st

from utils.eligibility import parse_age_bounds, verify_age_rule
from utils.live_search import find_hackathons

st.set_page_config(page_title="Hackathon Finder AI", page_icon="🔎", layout="wide")
st.title("🔎 Live Hackathon Finder")
st.write("Find individual hackathon events in your preferred time period.")
st.caption("Search results may be incomplete or outdated. Confirm event dates and eligibility on the organizer's official page.")

left, right = st.columns(2)
with left:
    interests = st.text_input("Interests / technologies", placeholder="AI, Python, climate, social good")
    details = st.text_area("Other details", placeholder="Beginner-friendly, virtual, free, teams of 2–3", height=120)
    age = st.number_input("Your age (used only for local comparison)", min_value=13, max_value=99, value=16)
with right:
    start_date = st.date_input("Earliest event date", key="period_start")
    end_date = st.date_input("Latest event date", key="period_end")
    use_ollama = st.checkbox("Use local Ollama AI summaries", value=True, help="AI runs only if Ollama and its model are installed on the same machine as this app. Search still works without it.")

if age < 18:
    st.warning("Some events require parental consent or have additional eligibility rules for minors.")

if st.button("Search for hackathons", type="primary", use_container_width=True):
    if not interests.strip() and not details.strip():
        st.warning("Enter interests or describe the hackathon you want.")
    elif start_date > end_date:
        st.error("The start date must be on or before the latest date.")
    else:
        with st.spinner("Searching event pages and filtering directories, guides, duplicates, and past listings..."):
            st.session_state["live_search_result"] = find_hackathons(interests, details, start_date, end_date, use_ollama=use_ollama)

result = st.session_state.get("live_search_result")
if result:
    if result.get("error"):
        st.error(result.get("message", "Search failed."))
    elif not result.get("results"):
        st.info(result.get("message", "No individual event pages were found."))
        with st.expander("Search diagnostics"):
            st.json(result.get("search_diagnostics", {}))
    else:
        st.success(f"Found {len(result['results'])} individual event-page candidates after filtering and deduplication.")
        if result.get("ai_available"):
            st.caption("Local Ollama added brief relevance explanations. It did not verify dates or eligibility.")
        elif use_ollama:
            st.warning(result.get("ai_message", "Ollama is unavailable; using local ranking."))
        else:
            st.caption("Using the built-in free local ranker; Ollama is optional.")

        for item in result["results"]:
            st.markdown(f"### {item['name']}")
            st.write(item.get("reason", "Potential event page; verify details."))
            st.caption(item.get("date_match", "Date not confirmed"))
            if item.get("snippet"):
                st.write(item["snippet"])
            st.link_button("Open event page/source", item["url"])
            key = hashlib.sha256(item["url"].encode()).hexdigest()[:12]
            with st.expander("Official page and age-rule review"):
                st.markdown(f"**Source:** {item['url']}")
                st.caption("Confirm this is the event organizer's official page.")
                if st.button("Fetch possible age-rule evidence", key=f"fetch_{key}"):
                    with st.spinner("Fetching page text..."):
                        st.session_state[f"age_evidence_{key}"] = verify_age_rule(item["url"])
                evidence = st.session_state.get(f"age_evidence_{key}")
                if evidence:
                    if evidence.get("error"):
                        st.warning(evidence["message"])
                    else:
                        st.caption(f"Fetched {evidence['checked_at']} UTC")
                        st.info(evidence["message"])
                        for sentence in evidence.get("evidence", []):
                            st.markdown(f"> {sentence}")
                        st.caption("This is evidence gathering only. Read and verify the official rules yourself.")
                st.markdown("**After reading the official rules, record your review (session only).**")
                low = st.text_input("Minimum age, if stated", key=f"min_{key}")
                high = st.text_input("Maximum age, if stated", key=f"max_{key}")
                no_limit = st.checkbox("I verified the official rules explicitly state no age limit", key=f"none_{key}")
                if st.button("Save reviewed age rule", key=f"save_{key}"):
                    try:
                        if not no_limit and not low.strip() and not high.strip():
                            raise ValueError("Enter an age bound or confirm an explicit no-age-limit rule.")
                        minimum, maximum = parse_age_bounds(low, high)
                        st.session_state[f"reviewed_{key}"] = {"min": minimum, "max": maximum, "none": no_limit}
                    except ValueError as exc:
                        st.error(str(exc))
                reviewed = st.session_state.get(f"reviewed_{key}")
                if reviewed:
                    if reviewed["none"]:
                        st.success("Your review: the official rules explicitly state no age limit.")
                    else:
                        min_age, max_age = reviewed["min"], reviewed["max"]
                        st.success(f"Your reviewed rule: minimum {min_age if min_age is not None else 'not stated'}; maximum {max_age if max_age is not None else 'not stated'}.")
                        matches = (min_age is None or int(age) >= min_age) and (max_age is None or int(age) <= max_age)
                        st.write("Your age matches the recorded rule." if matches else "Your age does not match the recorded rule.")
                    st.caption("Human-reviewed, session-only; this is not automatic certification.")
            st.divider()
