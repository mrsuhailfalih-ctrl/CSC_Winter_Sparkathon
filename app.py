import hashlib

import streamlit as st

from utils.eligibility import parse_age_bounds, verify_age_rule
from utils.live_search import find_hackathons


st.set_page_config(page_title="Hackathon Finder AI", page_icon="🔎", layout="wide")
st.title("🔎 Live Hackathon Finder")
st.write("Search the web for hackathons that fit your schedule and interests.")
st.caption("Live search results and AI summaries can be incomplete. Confirm dates, eligibility, costs, and registration details on the event's official page.")

left, right = st.columns(2)
with left:
    interests = st.text_input("Interests / technologies", placeholder="AI, Python, climate, social good")
    details = st.text_area(
        "What else are you looking for?",
        placeholder="Beginner-friendly, virtual, free registration, team of 3, high-school eligible...",
        height=120,
    )
    age = st.number_input("Your age (used only for your local comparison)", min_value=13, max_value=99, value=16, step=1)
with right:
    st.markdown("#### When can you participate?")
    start_date = st.date_input("Earliest event date", key="period_start")
    end_date = st.date_input("Latest event date", key="period_end")
    st.caption("The search query includes this period. Search results may not state event dates; verify them on each event page.")

if age < 18:
    st.warning("Some events require parental consent or have additional rules for minors.")

if st.button("Search live web", type="primary", use_container_width=True):
    if not interests.strip() and not details.strip():
        st.warning("Enter an interest or describe the hackathon you want.")
    elif start_date > end_date:
        st.error("The earliest date must be on or before the latest date.")
    else:
        with st.spinner("Searching the web and asking your local Ollama model to assess results..."):
            result = find_hackathons(interests, details, start_date, end_date)
        st.session_state["live_search_result"] = result

result = st.session_state.get("live_search_result")
if result:
    if result.get("error"):
        st.error(result.get("message", "Search failed."))
    elif not result.get("results"):
        st.info(result.get("message", "No results found."))
    else:
        if result.get("ai_available"):
            st.success("Live search completed; Ollama added a cautious relevance/date assessment.")
        else:
            st.warning("Live search completed, but Ollama was unavailable. Showing search results without AI assessment. Start Ollama and try again for local AI annotations.")
        st.caption("No numeric match scores are generated. Search-result pages are candidates, not verified official sources.")

        for item in result["results"]:
            st.markdown(f"### {item['name']}")
            st.write(item.get("reason", "Live search result; verify the page."))
            st.caption(item.get("date_match", "Event dates not confirmed"))
            st.write(item.get("snippet") or "No search snippet was supplied.")
            if item.get("url"):
                st.link_button("Open event/source page (confirm it is official)", item["url"])
            else:
                st.info("No event page URL was returned for this result.")

            stable_key = hashlib.sha256(item.get("url", item["id"]).encode("utf-8")).hexdigest()[:12]
            with st.expander("Official page and age-rule review"):
                if item.get("url"):
                    st.markdown(f"**Source URL:** {item['url']}")
                    st.caption("Confirm that this is the official event or rules page before relying on its contents.")
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
                            st.caption("Extracted text is only a clue. Read the official rules yourself; no evidence does not mean all ages are allowed.")
                else:
                    st.warning("No page URL is available, so age rules cannot be checked for this result.")

                st.markdown("**After reading the official rules, record your own review (session only).**")
                minimum_text = st.text_input("Minimum age, if stated", key=f"min_age_{stable_key}")
                maximum_text = st.text_input("Maximum age, if stated", key=f"max_age_{stable_key}")
                no_age_limit = st.checkbox("I verified the official rules explicitly state no age limit", key=f"no_age_limit_{stable_key}")
                if st.button("Save reviewed age rule", key=f"save_age_{stable_key}"):
                    try:
                        if not no_age_limit and not minimum_text.strip() and not maximum_text.strip():
                            raise ValueError("Enter an age bound or confirm an explicit no-age-limit rule.")
                        minimum, maximum = parse_age_bounds(minimum_text, maximum_text)
                        st.session_state[f"reviewed_age_{stable_key}"] = {
                            "minimum": minimum,
                            "maximum": maximum,
                            "no_limit": no_age_limit,
                            "url": item.get("url", ""),
                        }
                    except ValueError as exc:
                        st.error(str(exc))

                reviewed = st.session_state.get(f"reviewed_age_{stable_key}")
                if reviewed:
                    if reviewed["no_limit"]:
                        st.success("Your review: the official rules explicitly state no age limit.")
                    else:
                        min_label = reviewed["minimum"] if reviewed["minimum"] is not None else "not stated"
                        max_label = reviewed["maximum"] if reviewed["maximum"] is not None else "not stated"
                        st.success(f"Your reviewed rule: minimum {min_label}; maximum {max_label}.")
                        matches_age = (reviewed["minimum"] is None or int(age) >= reviewed["minimum"]) and (reviewed["maximum"] is None or int(age) <= reviewed["maximum"])
                        st.write("Your age matches the rule you recorded." if matches_age else "Your age does not match the rule you recorded.")
                    st.caption("Human-reviewed, session-only; this is not automatic eligibility certification.")
            st.divider()
