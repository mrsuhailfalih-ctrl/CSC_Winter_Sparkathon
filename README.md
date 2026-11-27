# Hackathon Finder AI

A browser-based hackathon finder built with Streamlit. Once the app is deployed, visitors open its link and search immediately—no Python, Ollama, API key, or separate downloads are required on their devices.

## Open the app

Use the public app URL provided by the person who deployed it. Enter interests and a date range, then select **Search for hackathons**. OpenRouter AI ranking is optional and disabled by default; the finder works without an AI key or a locally installed model.

> Search listings are candidates, not guarantees. Check dates, eligibility, and registration on the organizer's official page. Public search providers may be incomplete or temporarily unavailable.

## Deploy once for browser access

Deployment is a one-time setup by the app owner; visitors do not repeat it or install dependencies. For a 14-year-old project owner, ask a parent/guardian to review the hosting provider's current age and account terms and manage deployment if required.

1. Push this repository to GitHub.
2. The account owner opens [Streamlit Community Cloud](https://share.streamlit.io/) and connects the repository, following the host's current account requirements.
3. Create an app using this repository's `main` branch and `app.py` as the entry point.
4. Deploy. The host installs the Python packages listed in `requirements.txt` automatically.
5. Share the resulting app URL. Later commits to the configured branch are deployed by the host automatically.

No secrets are needed for the default search and local ranking. Do not configure an AI API key unless the account owner has checked the provider's age, billing, and usage terms. Never commit secrets to the repository. Ollama is not part of the hosted workflow and visitors do not need to install it.

## Run locally (for development only)

You only need to install these tools on the computer used for development—not on every visitor's device:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Windows PowerShell activation: `.venv\\Scripts\\Activate.ps1`.

## Optional OpenRouter AI ranking

AI ranking is optional. If enabled, the server needs an OpenRouter API key supplied through its secret manager or environment; visitors should never provide or see that key. Only configure this after an adult account owner reviews the provider's current terms, age requirements, free-tier limits, and possible charges. With AI disabled or unavailable, search and local ranking continue to work.

## Search and eligibility

The app discovers candidates through public web search and applies local filters. Search may be rate-limited, outdated, or incomplete. It does not certify event dates or age eligibility. Open each organizer's official page and verify the rules yourself.

## Tests

```bash
python -m unittest discover -s tests -v
```
