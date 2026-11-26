# Hackathon Finder AI

Streamlit app for live hackathon discovery. It filters editorial guides, FAQs, directories, normalizes tracking links, and deduplicates results that appear to describe the same event. It uses Ollama locally for optional short relevance notes; search, filtering, and age review remain available if Ollama is offline.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
ollama pull qwen2.5:7b
ollama serve
```

In another terminal:

```bash
streamlit run app.py
```

Windows activation: `.venv\\Scripts\\Activate.ps1`.

If Ollama reports unavailable, verify it is running and the model is installed:

```bash
ollama list
ollama pull qwen2.5:7b
```

Ollama is local and does not require an API key. Live web search uses the `ddgs` client and its public upstream service; rate limits and availability can change.

## Search quality

- Enter a requested date range, interests, and additional preferences.
- The search makes focused queries and filters obvious guides, FAQs, directories, and news pages.
- Tracking parameters/fragments are removed, and near-duplicate event titles are merged to one result/link.
- Dates are only matched when a date is explicitly present in returned search text. Otherwise they remain unconfirmed.
- Ollama adds a short explanation, not a match score. Its output cannot establish event dates or age eligibility.
- Search-result URLs may not be official. Open and confirm the organizer's event page.

## Age-rule review

Every result retains an official-page and age-rule review section. Fetch possible age-related text, read the organizer's rules, and record the age bounds yourself. The app compares your age with only your human-entered rule. Reviews are session-only and are not an eligibility certification.

## Tests

```bash
python -m unittest discover -s tests -v
```

Search snippets can be outdated or misleading. Confirm event dates, age restrictions, costs, and registration status on organizer pages.
