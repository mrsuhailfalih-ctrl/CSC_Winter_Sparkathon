# AI Hackathon Finder

A Streamlit app for discovering hackathons. Its main workflow uses Backboard AI to search for events based on your prompt and preferences; a small clearly labeled sample dataset is available for offline browsing. The app does not match teammates.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

## Configure Backboard AI

Create a local `.env` file in the project root (do not commit it):

```text
BACKBOARD_API_KEY=your_key_here
# Optional, if your Backboard account uses a different endpoint:
BACKBOARD_API_URL=https://your-backboard-endpoint
```

On Streamlit Community Cloud, add the same values under **App settings → Secrets**:

```toml
BACKBOARD_API_KEY = "your_key_here"
# BACKBOARD_API_URL = "https://your-backboard-endpoint"
```

The API endpoint and request fields are configurable/in `utils/ai_engine.py`; confirm them against the endpoint and API schema provided by Backboard. When AI is not configured or unavailable, the app still lets you search and filter the sample dataset. Sample listings are illustrative, not verified current events.
