import streamlit as st

from utils.ai_engine import recommend_hackathons


st.set_page_config(page_title="Hackathon Finder AI", page_icon="🔎", layout="wide")

st.title("🔎 Hackathon Finder AI")
st.write("Discover hackathons that match your interests, experience, and age.")
st.caption("Recommendations use a local starter dataset. AI and cached data can be incomplete—verify every rule on the official event page.")

left, right = st.columns([1, 1])

with left:
    age = st.number_input("Your age", min_value=13, max_value=99, value=16, step=1)
    interests = st.text_area(
        "Interests and preferred technologies",
        placeholder="AI, Python, climate, social good, web development",
        height=110,
    )
    experience = st.selectbox("Experience level", ["Beginner", "Intermediate", "Advanced"])

with right:
    location = st.radio("Location", ["Online", "In-person", "No preference"], horizontal=True)
    theme = st.text_input("Theme or cause", placeholder="Healthcare, education, climate")
    team_size = st.selectbox("Team size", ["1", "2", "3", "4+"])
    provider = st.selectbox("Recommendation engine", ["Local (free/offline)", "Ollama (local)", "Backboard"])

provider_key = {
    "Local (free/offline)": "local",
    "Ollama (local)": "ollama",
    "Backboard": "backboard",
}.get(provider, "local")

if age < 18:
    st.warning("If you are under 18, some events may require parental consent or have additional student eligibility rules.")

preferences = (
    f"Interests: {interests.strip()}\n"
    f"Experience: {experience}\n"
    f"Location: {location}\n"
    f"Theme: {theme.strip()}\n"
    f"Team size: {team_size}"
)

if st.button("Recommend hackathons", type="primary", use_container_width=True):
    if not interests.strip() and not theme.strip():
        st.warning("Add at least one interest or theme.")
    else:
        with st.spinner("Checking age eligibility and ranking matches..."):
            result = recommend_hackathons(preferences, int(age), provider_key)

        if result.get("error"):
            st.error(result.get("message", "Recommendation failed."))
        elif isinstance(result.get("answer"), list):
            matches = result["answer"]
            if not matches:
                st.info(result.get("message", "No eligible matches were found."))
            else:
                st.subheader(f"{len(matches)} potential matches")
                for event in matches:
                    st.markdown(f"### {event.get('name', 'Unknown event')}")
                    left_card, right_card = st.columns([3, 1])
                    with left_card:
                        st.write(event.get("reason", "Potential match."))
                        st.caption(
                            f"{event.get('location', 'Location unknown')} • "
                            f"{event.get('dates', 'Dates unknown')} • "
                            f"{event.get('level', 'Level unknown')}"
                        )
                        eligibility = event.get("eligibility") or event.get("age_label")
                        st.caption(f"Eligibility: {eligibility or 'Not provided—verify officially'}")
                    with right_card:
                        st.metric("Match score", f"{event.get('score', 0)}%")
                        if event.get("url"):
                            st.link_button("Official page", event["url"])
                    st.divider()
        elif isinstance(result.get("answer"), str):
            st.markdown(result["answer"])
            if result.get("sources"):
                st.caption("Sources: " + " • ".join(str(url) for url in result["sources"] if url))
        else:
            st.error("Unexpected recommendation response.")
