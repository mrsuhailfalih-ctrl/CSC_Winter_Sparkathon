# Hackathon Finder

The app checks public event-hosting platform pages for structured event listings. It no longer uses DuckDuckGo, another general search engine, or general web-result snippets.

## What the app does

1. Enter interests/preferences and a date range.
2. The server checks the public browse pages of Devpost, Devfolio, MLH, Unstop, Eventbrite, and Luma.
3. Where the platform page exposes event links and Schema.org `Event` JSON-LD, the app reads a small number of individual event pages and extracts title, dates, description, and location.
4. It displays only links on the corresponding official platform domains, and filters known dates outside the selected period. Events with no structured date are labeled unverified.

Coverage is best-effort, not comprehensive. Some platforms render listings in JavaScript, have no public unauthenticated API, or may limit automated access. If a source returns no data, the app reports that in diagnostics rather than quietly falling back to DuckDuckGo or inventing events. Check each event's organizer page for the current schedule, registration, and eligibility. Automated access should comply with the platforms' terms and robots rules.

## Deploy once for browser access

Visitors need only the deployed app URL. They do not install Python, Ollama, or search-provider credentials. A minor project owner should have a parent/guardian review the hosting provider's current account requirements and manage deployment if necessary.

1. Push the repository to GitHub.
2. Connect it to a compatible Streamlit host, set `app.py` as the entry point, and deploy.
3. Share the resulting app URL. The host installs dependencies from `requirements.txt`.

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
