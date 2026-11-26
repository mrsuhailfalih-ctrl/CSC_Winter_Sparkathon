# Hackathon Finder AI

A focused Streamlit AI assistant: describe the hackathon you want, and it recommends relevant events. It does not include teammate matching, sample listings, or other discovery tools. Recommendations depend on Backboard AI and its web-search capability; verify event details with the official organizer.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Git Bash/macOS/Linux; Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

## Configure Backboard AI

Create a `.env` file next to `app.py` (keep it private and do not commit it):

```text
BACKBOARD_API_KEY=your_key_here
# Optional if your account uses a different endpoint:
BACKBOARD_API_URL=https://your-backboard-endpoint
```

The Backboard endpoint and request fields in `utils/ai_engine.py` must match the API schema for your account.
