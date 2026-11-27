# Hackathon Finder AI

## Run

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Windows PowerShell activation: `.venv\\Scripts\\Activate.ps1`.

## Optional OpenRouter AI ranking

The app can use OpenRouter's `google/gemma-4-26b-a4b-it:free` model to score and explain search candidates. Search and deterministic local ranking continue to work if AI is disabled, the API key is missing, the model is unavailable, or a free-tier limit is reached.

1. Create an OpenRouter API key under an account that is eligible under OpenRouter's current terms. A parent or guardian should review account eligibility and supervise use for anyone under 18.
2. In local development, create `.streamlit/secrets.toml` (this file must not be committed) with:

```toml
OPENROUTER_API_KEY = "your-key-here"
```

   Or set `OPENROUTER_API_KEY` in the server environment. Streamlit Community Cloud: add the same key in the app's **Settings → Secrets**.
3. Run the app and leave **Use OpenRouter AI relevance ranking** enabled.

The key is only read by the Python server and is sent to OpenRouter's API; it is never included in the page or result data. Optional `OPENROUTER_MODEL` overrides the model ID. Free access and rate limits may change. The app sends only event search titles/snippets and requested dates, limits output size, and validates returned candidate IDs before using explanations/scores.

## Search and eligibility

Search uses public web results, targets individual event pages, and filters obvious directories, guides, and stale editions. Search can be rate-limited or inaccurate; confirm dates, registration, and eligibility on the organizer's official page. Age-rule extraction is only a clue, not an eligibility decision.

## Tests

```bash
python -m unittest discover -s tests -v
```
