# Hackathon Finder AI

A focused Streamlit app that uses Backboard to help users find hackathons matching their preferences. The app does not have live web browsing, so verify dates, eligibility, deadlines, costs, and registration links on official event pages.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Git Bash/macOS/Linux; Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

## Configure Backboard

1. In your Backboard dashboard, create an API key and choose a model/provider. Check the model's price and your credit balance before using it; a $5 balance does not guarantee a particular number of requests.
2. In the project folder, create or edit a local `.env` file (ignored by Git) with the key and exact provider/model values shown by Backboard:

```text
BACKBOARD_API_KEY=your_backboard_key
BACKBOARD_LLM_PROVIDER=provider_from_backboard
BACKBOARD_MODEL_NAME=model_name_from_backboard
```

The app requires an explicit provider and model rather than silently selecting a potentially more expensive default. It sends concise prompts, but actual charges depend on the selected model and Backboard's current pricing. Keep the key private: never paste it into chat or commit it to GitHub. See [Backboard's model documentation](https://docs.backboard.io/concepts/models) and [Send Message API reference](https://docs.backboard.io/api-reference/threads/send-message) for current model names and request details.
