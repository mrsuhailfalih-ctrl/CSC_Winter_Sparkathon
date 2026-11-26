import streamlit as st

from utils.ai_engine import query_gemini_ai

st.set_page_config(page_title="Hackathon Finder AI", page_icon="🔎", layout="centered")
st.title("🔎 Hackathon Finder AI")
st.write("Tell me what kind of hackathon you want, and I’ll recommend events that fit.")
st.caption("Recommendations are AI-generated. Confirm dates, eligibility, and deadlines on the official event pages.")

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
            result = query_gemini_ai(query.strip())

        if result.get("error"):
            st.error(result["message"])
        else:
            st.markdown(result["answer"])
            if result.get("sources"):
                st.subheader("Sources")
                for source in result["sources"]:
                    st.markdown(f"- [{source['title']}]({source['url']})")
