import json
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.ai_engine import query_backboard_ai
from utils.matcher import find_teammates

st.set_page_config(
    page_title="AI Hackathon Finder",
    page_icon="⚡",
    layout="wide",
)

DATA_DIR = Path(__file__).parent / "data"


@st.cache_data
def load_json(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as file:
        return json.load(file)


st.title("⚡ AI Hackathon Finder & Teammate Matcher")
st.markdown(
    "Find beginner-friendly hackathons, build a balanced team, "
    "and generate a practical project idea."
)

hackathons = load_json("hackathons.json")
teammates = load_json("teammates.json")

st.sidebar.header("Your Hacker Profile")
name = st.sidebar.text_input("First Name", "Alex")
experience = st.sidebar.selectbox(
    "Experience Level",
    ["First-Timer", "Beginner", "Intermediate"],
)
skills = st.sidebar.multiselect(
    "Your Skills",
    ["Python", "React", "HTML/CSS", "Figma", "Machine Learning", "Pitching"],
    default=["Python", "HTML/CSS"],
)
looking_for = st.sidebar.radio("Looking For", ["Teammates", "Mentor", "Both"])

user_profile = {
    "name": name,
    "experience": experience,
    "skills": skills,
    "lookingFor": looking_for,
}

st.sidebar.divider()
st.sidebar.caption("MVP for CSC Winter Sparkathon")

st.subheader("🤖 AI Vibe & Skill Matcher")
user_query = st.text_area(
    "Describe what you're looking for:",
    "Find a chill online weekend hackathon for beginners where I can learn Python.",
)

if st.button("Find My Match", type="primary", use_container_width=True):
    if not user_query.strip():
        st.warning("Describe what kind of hackathon or team you want first.")
    else:
        with st.spinner("Searching and matching..."):
            ai_result = query_backboard_ai(user_query, user_profile)

        if ai_result.get("error"):
            st.info(ai_result["message"])
        else:
            st.success("AI match generated")
            st.write(ai_result)

st.divider()
st.subheader("📅 Featured Student Hackathons")

col1, col2, col3 = st.columns(3)
with col1:
    format_filter = st.selectbox("Format", ["All", "Virtual", "In-Person"])
with col2:
    level_filter = st.selectbox("Difficulty", ["All", "Beginner", "All Levels"])
with col3:
    search = st.text_input("Search")

filtered = pd.DataFrame(hackathons)
if format_filter != "All":
    filtered = filtered[filtered["format"] == format_filter]
if level_filter != "All":
    filtered = filtered[filtered["level"] == level_filter]
if search:
    haystack = filtered[["name", "theme", "tags"]].astype(str).agg(" ".join, axis=1)
    filtered = filtered[haystack.str.contains(search, case=False, na=False)]

st.dataframe(filtered, use_container_width=True, hide_index=True)

st.divider()
st.subheader("🤝 Suggested Teammates")
matches = find_teammates(skills, teammates)

if not matches:
    st.info("Add a few skills to see teammate matches.")
else:
    for match in matches:
        with st.container(border=True):
            st.markdown(f"**{match['name']}** — {match['role']}")
            st.write(
                f"Skills: {', '.join(match['skills'])}\n\n"
                f"Why they fit: {match['match_reason']}"
            )
