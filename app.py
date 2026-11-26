import json
from pathlib import Path

import streamlit as st

from utils.ai_engine import query_backboard_ai

st.set_page_config(page_title="Hackathon Finder AI", page_icon="🔎", layout="wide")
DATA_DIR = Path(__file__).parent / "data"


@st.cache_data
def load_hackathons():
    with open(DATA_DIR / "hackathons.json", encoding="utf-8") as file:
        return json.load(file)


def display_ai_result(result):
    """Show a readable text field when available, otherwise show the response."""
    if isinstance(result, str):
        st.markdown(result)
        return
    if isinstance(result, dict):
        for key in ("response", "answer", "content", "message", "text"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                st.markdown(value)
                other_fields = {
                    name: item for name, item in result.items()
                    if name not in {key, "error"}
                }
                if other_fields:
                    with st.expander("Additional response details"):
                        st.json(other_fields)
                return
    st.json(result)


st.title("🔎 Find Your Next Hackathon")
st.markdown(
    "Describe the event you want. AI can look for current opportunities and "
    "summarize the dates, eligibility, cost, format, and official links. "
    "Always verify deadlines and details on the organizer’s website."
)

with st.sidebar:
    st.header("Your preferences")
    location = st.text_input("Location", placeholder="Online, Seattle, or anywhere")
    experience = st.selectbox(
        "Experience level", ["Any", "First-time", "Beginner", "Intermediate", "Advanced"]
    )
    interests = st.text_input("Topics or skills", placeholder="AI, climate, Python...")
    format_preference = st.selectbox("Format", ["Any", "Virtual", "In-person"])
    st.caption("AI search requires a configured Backboard API key.")

st.subheader("🤖 Search with AI")
query = st.text_area(
    "What kind of hackathon are you looking for?",
    placeholder="For example: a beginner-friendly online AI hackathon with registration still open.",
    height=100,
)

if st.button("Find hackathons", type="primary", width="stretch"):
    if not query.strip():
        st.warning("Enter a description of the hackathon you want to find.")
    else:
        preferences = {
            "location": location,
            "experience": experience,
            "interests": interests,
            "format": format_preference,
        }
        with st.spinner("Searching for relevant hackathons..."):
            result = query_backboard_ai(query, preferences)
        if isinstance(result, dict) and result.get("error"):
            st.warning(result["message"])
            st.info("Use the sample listings below while AI search is unavailable.")
        else:
            st.success("Search complete")
            display_ai_result(result)

st.divider()
st.subheader("📅 Browse sample listings")
st.caption(
    "These are illustrative seed records, not verified live events. "
    "Use AI search and confirm event details with organizers."
)

hackathons = load_hackathons()
col1, col2, col3 = st.columns(3)
with col1:
    format_filter = st.selectbox("Filter by format", ["All", "Virtual", "In-Person"])
with col2:
    level_filter = st.selectbox("Filter by experience", ["All", "Beginner", "All Levels"])
with col3:
    search = st.text_input("Filter sample listings", placeholder="Search name or topic")

filtered = hackathons
if format_filter != "All":
    filtered = [event for event in filtered if event.get("format") == format_filter]
if level_filter != "All":
    filtered = [event for event in filtered if event.get("level") == level_filter]
if search.strip():
    term = search.strip().casefold()
    filtered = [
        event for event in filtered
        if term in " ".join(str(value) for value in event.values()).casefold()
    ]

if filtered:
    st.dataframe(filtered, width="stretch", hide_index=True)
else:
    st.info("No sample listings match those filters.")
