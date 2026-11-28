from __future__ import annotations

import streamlit as st

from utils.luna_search import luna_is_configured, search_with_luna
from utils.search_filter import filter_search_results
from utils.serper_search import search_with_serper, serper_is_configured

st.set_page_config(page_title="Hackathon Finder", page_icon="⌁", layout="wide")

st.markdown("""
<style>
:root { --neon: #7c5cff; --cyan: #43d9ff; --ink: #090b14; --glass: rgba(17, 21, 38, 0.82); }
html, body, [class*="css"] { font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif; }
.stApp {
    background:
        radial-gradient(circle at 12% 12%, rgba(124,92,255,.22), transparent 25rem),
        radial-gradient(circle at 88% 18%, rgba(67,217,255,.10), transparent 22rem),
        linear-gradient(145deg, #090b14 0%, #0d1020 55%, #090b14 100%);
}
[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1180px; padding-top: 2.2rem; padding-bottom: 3rem; }
.hero {
    position: relative; overflow: hidden; border: 1px solid rgba(166,150,255,.24);
    border-radius: 24px; padding: 2rem 2.2rem; margin-bottom: 1.5rem;
    background: linear-gradient(120deg, rgba(124,92,255,.18), rgba(67,217,255,.05));
    box-shadow: 0 18px 60px rgba(0,0,0,.28), inset 0 1px rgba(255,255,255,.05);
}
.hero:after { content:""; position:absolute; width:260px; height:260px; right:-130px; top:-170px;
    border:1px solid rgba(67,217,255,.22); border-radius:50%; box-shadow:0 0 40px rgba(67,217,255,.08); }
.hero h1 { margin:0; font-size: clamp(2.25rem,5vw,4.3rem); letter-spacing:-.055em;
    background: linear-gradient(90deg,#fff 15%,#a99aff 62%,#43d9ff); -webkit-background-clip:text; color:transparent; }
.hero p { max-width:700px; color:#cbd0e8; font-size:1.02rem; margin:.7rem 0 0; }
.kicker { color:#43d9ff; font-size:.72rem; font-weight:800; letter-spacing:.18em; text-transform:uppercase; }
.search-panel, [data-testid="stContainer"] {
    border: 1px solid rgba(166,150,255,.18) !important; border-radius:18px !important;
    background: var(--glass) !important; box-shadow: 0 14px 38px rgba(0,0,0,.18); backdrop-filter: blur(14px);
}
.search-panel { padding:1.25rem 1.35rem; }
[data-testid="stContainer"] { padding:1.25rem; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input, [data-baseweb="select"] > div, [data-baseweb="input"] > div {
    background: rgba(8,10,20,.72) !important; border-color: rgba(166,150,255,.24) !important;
    border-radius:12px !important; color:#f4f6ff !important;
}
[data-testid="stDateInput"] input { border-radius:12px !important; }
.stButton > button, [data-testid="stLinkButton"] a {
    border:1px solid rgba(166,150,255,.38); border-radius:12px; min-height:44px;
    background: linear-gradient(100deg,#6651d9,#7c5cff 55%,#4abfdc); color:white;
    box-shadow:0 8px 28px rgba(124,92,255,.22); font-weight:750;
}
.stButton > button:hover, [data-testid="stLinkButton"] a:hover { border-color:#43d9ff; box-shadow:0 8px 30px rgba(67,217,255,.18); }
[data-testid="stSuccess"] { border:1px solid rgba(67,217,255,.22); background:rgba(67,217,255,.07); border-radius:12px; }
[data-testid="stInfo"] { border:1px solid rgba(124,92,255,.22); background:rgba(124,92,255,.07); border-radius:12px; }
[data-testid="stWarning"] { border:1px solid rgba(255,190,92,.20); background:rgba(255,190,92,.06); border-radius:12px; }
[data-testid="stCaptionContainer"] { color:#9da4c4; }
hr { border-color:rgba(166,150,255,.12); }
.result-grid { margin-top:.5rem; }
</style>

<div class="hero">
  <div class="kicker">NEXUS // EVENT DISCOVERY</div>
  <h1>Hackathon Finder</h1>
  <p>Search the live web for high-fit hackathons and let the AI filter signal from noise.</p>
</div>
""", unsafe_allow_html=True)

left, right = st.columns(2)
with left:
    interests = st.text_input("Interests / technologies", placeholder="AI, Python, climate, social good")
    details = st.text_area("Other preferences", placeholder="Free, beginner-friendly", height=100)
    age = st.number_input("Your age", min_value=5, max_value=100, value=18, step=1, help="Used to search for events that may fit your age. Confirm eligibility with organizers.")
with right:
    start_date = st.date_input("Earliest event date", key="period_start")
    end_date = st.date_input("Latest event date", key="period_end")
    event_format = st.selectbox("Hackathon format", ("Any", "Online", "In-person"), index=0)
    location = st.text_input("Location / vicinity", placeholder="City, state/province, or country")

if not serper_is_configured() and not luna_is_configured():
    st.warning("Configure SERPER_API_KEY or LUNA_API_KEY in environment variables / Streamlit secrets to enable search.")
elif luna_is_configured():
    st.caption("GPT web search is configured. If unavailable, the app will try Serper when configured.")

if st.button("Find hackathons", type="primary", use_container_width=True):
    if not interests.strip() and not details.strip():
        st.warning("Enter at least one interest or preference.")
    elif start_date > end_date:
        st.error("The earliest date must be on or before the latest date.")
    elif event_format == "In-person" and not location.strip():
        st.warning("Enter a location for in-person events.")
    else:
        args = dict(age=int(age), event_format=event_format, location=location)
        with st.spinner("Scanning live event signals..."):
            if luna_is_configured():
                result = search_with_luna(interests, details, start_date, end_date, **args)
                if result.get("error") and serper_is_configured():
                    st.warning(result["error"] + " Falling back to Serper search.")
                    result = search_with_serper(interests, details, start_date, end_date, **args)
                    result["search_provider"] = "Serper fallback"
                else:
                    result["search_provider"] = "GPT web search"
            elif serper_is_configured():
                result = search_with_serper(interests, details, start_date, end_date, **args)
                result["search_provider"] = "Serper"
            else:
                result = {"results": [], "error": "No search provider is configured."}
            st.session_state["search_result"] = result

result = st.session_state.get("search_result")
if result:
    if result.get("error"):
        st.error(result["error"])
    else:
        raw_results = result.get("results", [])
        events = filter_search_results(raw_results, start_date, end_date)
        removed = len(raw_results) - len(events)
        st.caption(f"Search provider: {result.get('search_provider', 'Search')}. Query: {result.get('query', '')}")
        st.info("Known event dates outside the selected range are hidden. Results without reliable dates remain visible as unverified.")
        if events:
            st.success(f"Showing {len(events)} result(s).")
            if removed:
                st.caption(f"Filtered out {removed} directory/roundup or confirmed out-of-range result(s).")
            for index, item in enumerate(events, start=1):
                with st.container(border=True):
                    st.markdown(f"### {index}. {item.get('title') or 'Untitled result'}")
                    verify = item.get("date_verification", {})
                    if verify.get("dates"):
                        st.caption("Date evidence: " + ", ".join(verify["dates"]) + " — confirm with organizer.")
                    else:
                        st.warning("Event dates could not be verified against the selected range.")
                    if item.get("event_start_date") or item.get("event_end_date"):
                        st.write(f"**Event schedule:** {item.get('event_start_date') or 'Unknown'} – {item.get('event_end_date') or item.get('event_start_date') or 'Unknown'}")
                    if item.get("format"):
                        st.write(f"**Format:** {item['format']}")
                    if item.get("location"):
                        st.write(f"**Location:** {item['location']}")
                    if item.get("age_eligibility"):
                        st.write(f"**Age eligibility:** {item['age_eligibility']}")
                    if item.get("snippet"):
                        st.write(item["snippet"])
                    if item.get("link"):
                        st.link_button("Open source page and verify", str(item["link"]))
        elif raw_results:
            st.info("No results remained after removing broad roundups and confirmed out-of-range events.")
        else:
            st.info("The search provider returned no event results.")

st.divider()
st.caption("Keep API keys private. Search preferences are sent to the configured AI/search provider. Verify dates, age eligibility, and event details with organizers.")
