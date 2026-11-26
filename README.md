# Hackathon Finder AI

A focused Streamlit app that uses Gemini to help users find hackathons matching their preferences. It does not require Google Search support, so it can work with Gemini models that support text generation. Without live web browsing, the AI cannot verify current event listings; check deadlines, eligibility, costs, and registration links on official event pages.

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

Keep the key private. Never paste it into chat, commit it, or put it in browser-side code. This app sends a text-generation request only; it does not require a model with Google Search grounding. Use the exact API model ID shown in AI Studio.
