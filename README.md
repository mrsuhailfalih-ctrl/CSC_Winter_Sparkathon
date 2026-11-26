# Hackathon Finder AI

A focused Streamlit app that uses Gemini to recommend hackathons from a user's request. If Google Search grounding is available for the selected Gemini model, it can look for current events and provide source links. Always verify details with event organizers.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Git Bash/macOS/Linux; Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

## Configure Gemini

1. With your parent/guardian's approval, create an API key in Google AI Studio and check the current usage/age terms and free-tier availability for your account.
2. In the project folder, create a local `.env` file (it is ignored by Git) with the key and a model ID available to your key:

```text
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=model-id-from-ai-studio
```

Keep the key private. Never paste it into chat, commit it, or put it in browser-side code. Google Search grounding must be supported for the model and API project; if the request returns an error, check the model's tool support and your AI Studio quota/settings.
