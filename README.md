# Hackathon Finder

A small browser-based directory that helps you search hackathons directly on event-hosting platforms. It intentionally does not use DuckDuckGo or another general-purpose search engine, and it does not scrape aggregator snippets and present them as verified events.

## Open the app

Open the deployed app URL, enter interests/preferences and a date range, then select **Show official event platforms**. Copy the prepared search phrase, open a platform, and use that platform's own search/date filters. Check each event's organizer page for dates, registration, location, and age eligibility.

Included source portals: Devpost, Devfolio, Major League Hacking (MLH), Unstop, Eventbrite, and Luma.

**Important limitation:** These platforms do not provide one shared, public, unauthenticated API for searching all listings. This app therefore links directly to the platforms rather than claiming to automatically retrieve or verify their events. The links are official platform pages, but individual listings still need human verification.

## Deploy once for browser access

Deployment is a one-time setup by the app owner; visitors do not need to install Python, Ollama, or an API key. For a minor project owner, have a parent/guardian check the hosting provider's current account and age requirements and manage deployment if necessary.

1. Push this repository to GitHub.
2. The account owner connects it to Streamlit Community Cloud (or another compatible Streamlit host).
3. Set the entry point to `app.py` and deploy. The host installs `requirements.txt`.
4. Share the resulting app URL.

No search-provider credentials or AI keys are required.

## Run locally for development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Windows PowerShell activation: `.venv\\Scripts\\Activate.ps1`.

## Tests

```bash
python -m unittest discover -s tests -v
```
