# Hackathon Finder

The finder checks public pages on Devpost, Devfolio, MLH, Unstop, Eventbrite, and Luma only—no DuckDuckGo or general web search.

It first looks for event links and Schema.org Event data, then falls back to event-page Open Graph/title/description metadata when structured event data is absent. Events with no readable date are retained and labeled as date-unverified instead of being silently discarded. The app only presents URLs from the allowlisted event platforms.

Platform pages may block automated requests, render event lists in JavaScript, or omit dates/metadata. In those cases source diagnostics explain the limitation; the finder cannot promise exhaustive results. Verify dates, registration, and age eligibility on the organizer's page.

## Run locally

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
