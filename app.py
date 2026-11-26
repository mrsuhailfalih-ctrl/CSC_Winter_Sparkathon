import streamlit as st

from utils.ai_engine import query_backboard_ai

st.set_page_config(page_title="Hackathon Finder AI", page_icon="🔎", layout="centered")
st.title("🔎 Hackathon Finder AI")
st.write("Tell me what kind of hackathon you want, and I’ll recommend events that fit.")
st.caption("AI suggestions may not be current or verified. Confirm event details on official pages.")

query = st.text_area(
    "What are you looking for?",
    placeholder=(
        "For example: beginner-friendly AI hackathons online, happening this summer, "
        "with free registration."
    ),
    height=140,
)

if st.button("Recommend hackathons", type="primary", use_container_width=True):
    if not query.strip():
        st.warning("Describe the hackathon you’re looking for.")
    else:
        with st.spinner("Finding hackathons that fit your request..."):
            result = query_backboard_ai(query.strip())

        if isinstance(result, dict) and result.get("error"):
            st.error(result.get("message", "Backboard request failed. Please try again."))
        elif isinstance(result, dict) and isinstance(result.get("answer"), str):
            st.markdown(result["answer"])
        elif isinstance(result, str):
            st.markdown(result)
        else:
            st.error("Backboard returned an unexpected response. Please try again.")
