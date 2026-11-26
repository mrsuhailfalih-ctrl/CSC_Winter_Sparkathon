import streamlit as st

from utils.ai_engine import query_backboard_ai

st.set_page_config(page_title="Hackathon Finder AI", page_icon="🔎", layout="centered")

st.title("🔎 Hackathon Finder AI")
st.write("Tell me what kind of hackathon you want, and I’ll recommend events that fit.")

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
            st.error(result["message"])
        elif isinstance(result, str):
            st.markdown(result)
        elif isinstance(result, dict):
            answer = next(
                (
                    result[key]
                    for key in ("response", "answer", "content", "message", "text")
                    if isinstance(result.get(key), str) and result[key].strip()
                ),
                None,
            )
            if answer:
                st.markdown(answer)
            else:
                st.error("The AI returned an unexpected response. Please try again.")
        else:
            st.error("The AI returned an unexpected response. Please try again.")
