import streamlit as st

from utils.ai_engine import recommend_hackathons
from utils.eligibility import parse_age_bounds, verify_age_rule


st.set_page_config(page_title="Hackathon Finder AI", page_icon="🔎", layout="wide")

st.title("🔎 Hackathon Finder AI")
st.write("Discover hackathons that match your interests, experience, and age.")
st.caption("Recommendations use a local starter dataset. Verify dates and eligibility on official event pages.")

left, right = st.columns([1, 1])

with left:
    age = st.number_input("Your age", min_value=13, max_value=99, value=16, step=1)
    interests = st.text_area("Interests and preferred technologies", placeholder="AI, Python, climate, social good, web development", height=110)
    experience = st.selectbox("Experience level", ["Beginner", "Intermediate", "Advanced"])

with right:
    location = st.radio("Location", ["Online", "In-person", "No preference"], horizontal=True)
    theme = st.text_input("Theme or cause", placeholder="Healthcare, education, climate")
    team_size = st.selectbox("Team size", ["1", "2", "3", "4+"])
    provider = st.selectbox("Recommendation engine", ["Local (free/offline)", "Ollama (local)", "Backboard"])

provider_key = {"Local (free/offline)": "local", "Ollama (local)": "ollama", "Backboard": "backboard"}[provider]

if age < 18:
    st.warning("If you are under 18, some events may require parental consent or additional eligibility rules.")

preferences = (
    f"Interests: {interests.strip()}\nExperience: {experience}\nLocation: {location}\n"
    f"Theme: {theme.strip()}\nTeam size: {team_size}"
)

if st.button("Recommend hackathons", type="primary", use_container_width=True):
    if not interests.strip() and not theme.strip():
        st.warning("Add at least one interest or theme.")
    else:
        with st.spinner("Checking available data and ranking matches..."):
            result = recommend_hackathons(preferences, int(age), provider_key)
        if result.get("error"):
            st.error(result.get("message", "Recommendation failed."))
        elif isinstance(result.get("answer"), list):
            matches = result["answer"]
            if not matches:
                st.info(result.get("message", "No matches were found."))
            else:
                st.subheader(f"{len(matches)} potential matches")
                for index, event in enumerate(matches):
                    st.markdown(f"### {event.get('name', 'Unknown event')}")
                    left_card, right_card = st.columns([3, 1])
                    with left_card:
                        st.write(event.get("reason", "Potential match."))
                        st.caption(f"{event.get('location', 'Location unknown')} • {event.get('dates', 'Dates unknown')} • {event.get('level', 'Level unknown')}")
                        st.caption(f"Eligibility: {event.get('eligibility') or event.get('age_label') or 'Unknown—verify on the official page'}")
                    with right_card:
                        st.metric("Match score", f"{event.get('score', 0)}%")
                        if event.get("url"):
                            st.link_button("Official page", event["url"])

                    url = event.get("url", "")
                    if url:
                        event_key = f"age_verify_{index}_{event.get('name', 'event')}"
                        with st.expander("Check age rule on the official page"):
                            st.caption("The checker only extracts possible evidence. It cannot certify eligibility; review the linked official rules yourself.")
                            if st.button("Fetch age-rule evidence", key=f"fetch_{event_key}"):
                                with st.spinner("Fetching the event page..."):
                                    st.session_state[f"evidence_{event_key}"] = verify_age_rule(url)
                            evidence_result = st.session_state.get(f"evidence_{event_key}")
                            if evidence_result:
                                if evidence_result.get("error"):
                                    st.warning(evidence_result["message"])
                                else:
                                    st.caption(f"Fetched {evidence_result['checked_at']} UTC from {evidence_result['url']}")
                                    st.info(evidence_result["message"])
                                    if evidence_result["evidence"]:
                                        for sentence in evidence_result["evidence"]:
                                            st.markdown(f"> {sentence}")
                                    else:
                                        st.warning("No evidence was extracted. Do not treat this as proof of unrestricted ages.")

                                    st.markdown("**After checking the official rules yourself, record the rule below.**")
                                    min_text = st.text_input("Minimum age (leave blank if none is stated)", key=f"min_{event_key}")
                                    max_text = st.text_input("Maximum age (leave blank if none is stated)", key=f"max_{event_key}")
                                    no_limit = st.checkbox("I confirmed the official rules explicitly allow all ages / state no age limit", key=f"none_{event_key}")
                                    if st.button("Save my reviewed rule", key=f"save_{event_key}"):
                                        try:
                                            if not no_limit and not min_text.strip() and not max_text.strip():
                                                raise ValueError("Enter at least one age bound, or confirm that the official rules explicitly state no age limit.")
                                            minimum, maximum = parse_age_bounds(min_text, max_text)
                                            st.session_state[f"verified_{event_key}"] = {
                                                "minimum_age": minimum,
                                                "maximum_age": maximum,
                                                "no_limit": no_limit,
                                                "source_url": url,
                                                "checked_at": evidence_result["checked_at"],
                                            }
                                            st.success("Saved as reviewed for this browser session. This is your review, not an automatic certification.")
                                        except ValueError as exc:
                                            st.error(str(exc))

                                    reviewed = st.session_state.get(f"verified_{event_key}")
                                    if reviewed:
                                        if reviewed["no_limit"]:
                                            st.success("Reviewed rule: official page explicitly states no age limit.")
                                        else:
                                            st.success(f"Reviewed rule: ages {reviewed['minimum_age'] if reviewed['minimum_age'] is not None else 'unspecified minimum'}–{reviewed['maximum_age'] if reviewed['maximum_age'] is not None else 'unspecified maximum'}.")
                                        in_range = (reviewed["minimum_age"] is None or int(age) >= reviewed["minimum_age"]) and (reviewed["maximum_age"] is None or int(age) <= reviewed["maximum_age"])
                                        st.write("Your age matches the rule you recorded." if in_range else "Your age does not match the rule you recorded.")
                                        st.caption("Session-only; re-check the official rules and update the dataset if you need this review to persist.")
                    st.divider()
        elif isinstance(result.get("answer"), str):
            st.markdown(result["answer"])
        else:
            st.error("Unexpected recommendation response.")
