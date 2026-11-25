# AI Hackathon Finder

A Streamlit app for the CSC Winter Sparkathon that helps students:

- discover beginner-friendly hackathons
- match with teammates based on complementary skills
- get AI-assisted search and project ideas
- use local sample data when the AI API is unavailable

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Backboard AI configuration

Create a local `.env` file:

```text
BACKBOARD_API_KEY=your_key_here
```

For Streamlit Community Cloud, add `BACKBOARD_API_KEY` under **App settings → Secrets** instead of committing a key.

The Backboard endpoint in `utils/ai_engine.py` may need adjustment to match the API details supplied for the hackathon.
