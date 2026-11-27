import hashlib
import re

import streamlit as st

from utils.eligibility import parse_age_bounds, verify_age_rule
from utils.live_search import find_hackathons
from utils.openrouter_ai import analyze_with_openrouter


def _words(text: str) -> set[str]:
    ignored = {"and", "the", "for", "with", "from", "that", "this", "any", "are", "you", "your", "want", "looking", "hackathon", "hackathons", "event", "events"}
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if (len(word) >= 3 or word == "ai") and word not in ignored}


def _has_topic_match(item: dict, interests: str) -> bool:
    terms = _words(interests)
    if not terms:
        return True
    evidence = f"{item.get('name', '')} {item.get('snippet', '')}".lower()
    evidence_terms = _words(evidence)
    if "ai" in terms and ("artificial" in evidence_terms or "intelligence" in evidence_terms):
        evidence_terms.add("ai")
    # Interests are alternatives (e.g. AI OR Python), not a requirement that every
    # search result snippet repeat every entered keyword.
    return bool(terms & evidence_terms)


def _preference_status(item: dict, details: str) -> list[str]:
    evidence = f"{item.get('name', '')} {item.get('snippet', '')}".lower()
    requested = _words(details)
    status = []
    if requested & {"online", "virtual", "remote"}:
        status.append("Online/virtual: mentioned" if re.search(r"\b(online|virtual|remote|remote-first|anywhere|worldwide)\b", evidence) else "Online/virtual: not confirmed")
    if "free" in requested:
        status.append("Free: mentioned" if re.search(r"\b(free|no cost|without charge|free to enter|free entry)\b", evidence) else "Free: not confirmed")
    return status


def _split_candidates(candidates: list[dict], interests: str) -> tuple[list[dict], list[dict]]:
    relevant = [item for item in candidates if _has_topic_match(item, interests)]
    # Never label unknown dates as in-range; keep them visible as unverified possibilities.
    confirmed = [item for item in relevant if item.get("date_fit") is True]
    possible = [item for item in relevant if item.get("date_fit") is None]
    return confirmed, possible


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
        help="Disabled by default to avoid free-tier rate limits. Search and local ranking work without AI.",
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
            # Exclude only events explicitly dated outside the requested period. Results
            # without date evidence are shown separately, never presented as confirmed.
            candidates = [item for item in result.get("results", []) if item.get("date_fit") is not False]
            confirmed, possible = _split_candidates(candidates, interests)
            result["confirmed_results"] = confirmed
            result["possible_results"] = possible
            if use_ai and (confirmed or possible):
                to_score = confirmed + possible
                with st.spinner("Scoring results with OpenRouter..."):
                    ai = analyze_with_openrouter(
                        to_score,
                        f"Interests: {interests}\nAdditional details: {details}",
                        start_date,
                        end_date,
                    )
                result["ai_available"] = ai["available"]
                result["ai_message"] = ai["message"]
                for item in to_score:
                    annotation = ai["annotations"].get(item["id"])
                    if annotation:
                        item["ai_score"] = annotation["score"]
                        item["reason"] = annotation["reason"]
                confirmed.sort(key=lambda item: -item.get("ai_score", item.get("local_relevance", 0)))
                possible.sort(key=lambda item: -item.get("ai_score", item.get("local_relevance", 0)))
            else:
                result["ai_available"] = False
                result["ai_message"] = "AI ranking is off; using local ranking."
            if not confirmed and not possible:
                result["message"] = "No relevant candidates were found. Try broader interests or a wider date range."
            result["results"] = confirmed + possible
            st.session_state["live_search_result"] = result

result = st.session_state.get("live_search_result")
if result:
    if result.get("error"):
        st.error(result.get("message", "Search failed."))
    elif not result.get("results"):
        st.info(result.get("message", "No individual event candidates were found."))
        with st.expander("Search diagnostics"):
            st.json(result.get("search_diagnostics", {}))
    else:
        confirmed = result.get("confirmed_results", [])
        possible = result.get("possible_results", [])
        if confirmed:
            st.success(f"{len(confirmed)} candidate(s) have date evidence inside your selected period.")
        if result.get("ai_available"):
            st.caption("OpenRouter added relevance ranking; it does not verify event details or eligibility.")
        elif use_ai and result.get("ai_message"):
            st.warning(result["ai_message"])
        else:
            st.caption("Using local relevance ranking. OpenRouter is optional and disabled by default.")

        def render_event(item: dict) -> None:
            st.markdown(f"### {item['name']}")
            if "ai_score" in item:
                st.caption(f"AI relevance: {item['ai_score']}/100")
            st.write(item.get("reason", "Potential event page; verify details."))
            st.caption(item.get("date_match", "Date not confirmed"))
            for note in _preference_status(item, details):
                st.caption(note)
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

        if confirmed:
            st.subheader("Date evidence in your selected range")
            for item in confirmed:
                render_event(item)
        if possible:
            st.subheader("Possible matches — dates need verification")
            st.warning("These results mention your interests but the search snippet does not confirm dates in your selected period. Check each event's official page before treating it as a match.")
            for item in possible:
                render_event(item)
