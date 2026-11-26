import hashlib

import streamlit as st

from utils.eligibility import parse_age_bounds, verify_age_rule
from utils.live_search import find_hackathons


st.set_page_config(page_title="Hackathon Finder AI", page_icon="🔎", layout="wide")
st.title("🔎 Live Hackathon Finder")
st.write("Search the web for hackathons in your preferred time period.")
st.caption("Search and AI summaries are not authoritative. Confirm event dates, eligibility, costs, and registration on the organizer's official page.")

left, right = st.columns(2)
with left:
    interests = st.text_input("Interests / technologies", placeholder="AI, Python, climate, social good")
    details = st.text_area("Other details", placeholder="For example: online, beginner-friendly, free, teams of 2–3", height=120)
    age = st.number_input("Your age (used only for local comparison)", min_value=13, max_value=99, value=16, step=1)
with right:
    st.markdown("#### When can you participate?")
    start_date = st.date_input("Earliest event date", key="period_start")
    end_date = st.date_input("Latest event date", key="period_end")
    use_ollama = st.checkbox("Use optional local Ollama AI summaries", value=False, help="Off by default so searching works without installing/running a model. Search and local ranking are always available for free.")

if age < 18:
    st.warning("Some events require parental consent or have additional rules for minors.")

if st.button("Search live web", type="primary", use_container_width=True):
    if not interests.strip() and not details.strip():
        st.warning("Enter an interest or describe the hackathon you want.")
    elif start_date > end_date:
        st.error("The earliest date must be on or before the latest date.")
    else:
        with st.spinner("Searching and filtering for specific event pages..."):
            st.session_state["live_search_result"] = find_hackathons(
                interests, details, start_date, end_date, use_ollama=use_ollama
            )

result = st.session_state.get("live_search_result")
if result:
    if result.get("error"):
        st.error(result.get("message", "Search failed."))
    elif not result.get("results"):
        st.info(result.get("message", "No specific event pages found."))
    else:
        st.success(f"Found {len(result['results'])} distinct event-page candidates after removing guides, FAQs, directories, and duplicate links.")
        if result.get("ai_available"):
            st.caption("Ollama added short relevance notes. Dates and eligibility still need official-page verification.")
        elif use_ollama and result.get("ai_message"):
            st.info(result["ai_message"] + " Search results remain available using the free local ranker.")
        else:
            st.caption("Using the built-in free local ranker. Ollama is optional and is not required for search.")
        st.caption("No generated scores. Results are deduplicated and ranked by explicit date evidence and matching terms; sources may not be official.")

        for item in result["results"]:
            st.markdown(f"### {item['name']}")
            st.write(item.get("reason", "Potential event page; verify details on the official site."))
            st.caption(item.get("date_match", "Event date not confirmed"))
            if item.get("snippet"):
                st.write(item["snippet"])
            if item.get("url"):
                st.link_button("Open event page / source", item["url"])

            stable_key = hashlib.sha256(item.get("url", item["id"]).encode("utf-8")).hexdigest()[:12]
            with st.expander("Official page and age-rule review"):
                if item.get("url"):
                    st.markdown(f"**Source:** {item['url']}")
                    st.caption("Confirm that this is the organizer's official page before relying on its rules.")
                    if st.button("Fetch possible age-rule evidence", key=f"fetch_age_{stable_key}"):
                        with st.spinner("Fetching page text..."):
                            st.session_state[f"age_evidence_{stable_key}"] = verify_age_rule(item["url"])
                    evidence = st.session_state.get(f"age_evidence_{stable_key}")
                    if evidence:
                        if evidence.get("error"):
                            st.warning(evidence["message"])
                        else:
                            st.caption(f"Fetched {evidence['checked_at']} UTC")
                            st.info(evidence["message"])
                            for sentence in evidence.get("evidence", []):
                                st.markdown(f"> {sentence}")
                            st.caption("This extraction is only a clue. Read the official rules yourself; no extracted text does not mean there is no restriction.")
                else:
                    st.warning("This result has no link, so its age rule cannot be checked.")

                st.markdown("**After reading the official rules, record your own review (session only).**")
                minimum_text = st.text_input("Minimum age, if stated", key=f"min_age_{stable_key}")
                maximum_text = st.text_input("Maximum age, if stated", key=f"max_age_{stable_key}")
                no_age_limit = st.checkbox("I verified the official rules explicitly state no age limit", key=f"no_age_limit_{stable_key}")
                if st.button("Save reviewed age rule", key=f"save_age_{stable_key}"):
                    try:
                        if not no_age_limit and not minimum_text.strip() and not maximum_text.strip():
                            raise ValueError("Enter an age bound or confirm an explicit no-age-limit rule.")
                        minimum, maximum = parse_age_bounds(minimum_text, maximum_text)
                        st.session_state[f"reviewed_age_{stable_key}"] = {"minimum": minimum, "maximum": maximum, "no_limit": no_age_limit}
                        st.success("Saved for this browser session; this is a human review, not automatic certification.")
                    except ValueError as exc:
                        st.error(str(exc))

                reviewed = st.session_state.get(f"reviewed_age_{stable_key}")
                if reviewed:
                    if reviewed["no_limit"]:
                        st.success("Your review: the official rules explicitly state no age limit.")
                    else:
                        minimum = reviewed["minimum"]
                        maximum = reviewed["maximum"]
                        st.success(f"Your reviewed rule: minimum {minimum if minimum is not None else 'not stated'}; maximum {maximum if maximum is not None else 'not stated'}.")
                        matches = (minimum is None or int(age) >= minimum) and (maximum is None or int(age) <= maximum)
                        st.write("Your age matches the rule you recorded." if matches else "Your age does not match the rule you recorded.")
                    st.caption("Human-reviewed, session-only; re-check current rules on the official page.")
            st.divider()
