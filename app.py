import hashlib
import re

import streamlit as st

from utils.eligibility import parse_age_bounds, verify_age_rule
from utils.live_search import find_hackathons
from utils.openrouter_ai import analyze_with_openrouter


def _preference_tokens(text: str) -> set[str]:
    ignored = {"and", "the", "for", "with", "from", "that", "this", "any", "are", "you", "your", "want", "looking", "hackathon", "hackathons", "event", "events"}
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if (len(word) >= 3 or word == "ai") and word not in ignored}


def _matches_search_preferences(item: dict, interests: str, details: str) -> bool:
    """Be conservative: require date evidence and every requested topic/constraint."""
    # Unknown dates are not evidence that an event is happening in the requested period.
    if item.get("date_fit") is not True:
        return False

    evidence = f"{item.get('name', '')} {item.get('snippet', '')}".lower()
    evidence_terms = _preference_tokens(evidence)
    interest_terms = _preference_tokens(interests)
    if "ai" in interest_terms and ("artificial" in evidence_terms or "intelligence" in evidence_terms):
        evidence_terms.add("ai")
    if not interest_terms.issubset(evidence_terms):
        return False

    detail_terms = _preference_tokens(details)
    if detail_terms & {"online", "virtual", "remote"}:
        if not re.search(r"\b(online|virtual|remote|remote-first|anywhere|worldwide)\b", evidence):
            return False
    if "free" in detail_terms:
        if not re.search(r"\b(free|no cost|without charge|free to enter|free entry)\b", evidence):
            return False
    # Enforce any other specific words the user provided too.
    remaining_details = detail_terms - {"online", "virtual", "remote", "free"}
    if not remaining_details.issubset(evidence_terms):
        return False
    return True


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
    use_ai = st.checkbox(
        "Use OpenRouter AI relevance ranking (optional)",
        value=False,
        help="Disabled by default to avoid free-tier rate limits. Deterministic filters and local ranking work without AI.",
    )

if age < 18:
    st.warning("Some events require parental consent or have additional eligibility rules for minors.")

if st.button("Search for hackathons", type="primary", use_container_width=True):
    if not interests.strip() and not details.strip():
        st.warning("Enter interests or describe the hackathon you want.")
    elif start_date > end_date:
        st.error("The start date must be on or before the latest date.")
    else:
        with st.spinner("Searching event pages and filtering directories, guides, duplicates, and past listings..."):
            result = find_hackathons(interests, details, start_date, end_date, use_ollama=False)
            if result.get("results"):
                before_filter = len(result["results"])
                result["results"] = [
                    item for item in result["results"]
                    if _matches_search_preferences(item, interests, details)
                ]
                result.setdefault("search_diagnostics", {})["preference_filtered_count"] = before_filter - len(result["results"])
            if use_ai and result.get("results"):
                with st.spinner("Scoring results with OpenRouter..."):
                    ai = analyze_with_openrouter(
                        result["results"],
                        f"Interests: {interests}\nAdditional details: {details}",
                        start_date,
                        end_date,
                    )
                result["ai_available"] = ai["available"]
                result["ai_message"] = ai["message"]
                for item in result["results"]:
                    annotation = ai["annotations"].get(item["id"])
                    if annotation:
                        item["ai_score"] = annotation["score"]
                        item["reason"] = annotation["reason"]
                result["results"].sort(
                    key=lambda item: -item.get("ai_score", item.get("local_relevance", 0))
                )
            else:
                result["ai_available"] = False
                result["ai_message"] = "AI ranking is off; using local ranking."
            if not result.get("results"):
                result["message"] = (
                    "No results had verified date evidence inside your selected period and matched all requested topics/constraints. "
                    "Try a wider date range or simpler preferences; the app omits events with unknown dates rather than guessing."
                )
            st.session_state["live_search_result"] = result

result = st.session_state.get("live_search_result")
if result:
    if result.get("error"):
        st.error(result.get("message", "Search failed."))
    elif not result.get("results"):
        st.info(result.get("message", "No individual event pages matched your interests and dates."))
        with st.expander("Search diagnostics"):
            st.json(result.get("search_diagnostics", {}))
    else:
        st.success(f"Showing {len(result['results'])} individual event-page candidates matched to your interests and date range.")
        if result.get("ai_available"):
            st.caption("OpenRouter added relevance scores. It does not verify event details or eligibility.")
        elif use_ai and result.get("ai_message"):
            st.warning(result["ai_message"])
        else:
            st.caption("Using deterministic date/topic filters and the built-in local ranker; OpenRouter is optional.")

        for item in result["results"]:
            st.markdown(f"### {item['name']}")
            if "ai_score" in item:
                st.caption(f"AI relevance: {item['ai_score']}/100")
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
