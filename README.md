# Hackathon Finder

A Streamlit app that searches the web for hackathons using Serper. The app has no Momen AI dependency. It preserves plausible search results when snippets omit details, clearly labeling dates, age eligibility, and format as unverified where appropriate.

## Configure Serper

Create a Serper API key and add it as a server-side secret. Do not expose it in browser code or commit it.

Local `.env` (optional; install/load it through your existing environment setup):

```dotenv
SERPER_API_KEY=your_serper_api_key
```

Streamlit Community Cloud `.streamlit/secrets.toml`:

```toml
SERPER_API_KEY = "your_serper_api_key"
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

On Windows PowerShell, activate with `.venv\\Scripts\\Activate.ps1`.

## Search and eligibility notes

The app searches using interests, preferences, requested date range, age, and online/in-person preference. Search criteria are hints, not proof: snippets may show a registration deadline rather than event dates. Candidates with unknown details are retained and labeled for manual verification. Candidates are excluded for age or format only when the snippet clearly suggests a conflict. The app cannot determine legal eligibility, parental-consent requirements, or current organizer rules.

Run tests with:

```bash
python -m unittest discover -s tests -v
```
