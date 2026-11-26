# Hackathon Finder AI

## Search produced no results?

The app now tries multiple progressively broader public-web queries and reports a useful message when none returns event pages. Try a wider date range and shorter terms such as `AI` or `student`. Public search is not guaranteed: the free upstream service can rate-limit or temporarily return no results.

Search results are filtered for obvious guide/news/archive pages, stale editions, and duplicate links. Because search snippets are imperfect, events without a clear date are retained but marked **date unconfirmed** rather than silently discarded. The app cannot guarantee every result is current—verify organizer pages.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Windows PowerShell: `.venv\\Scripts\\Activate.ps1`.

Search and ranking use free Python logic and the public `ddgs` search client. Optional Ollama summaries require Ollama and a model installed locally; the app works without it. There is no reliably available public LLM service that can be promised both effective and 100% free; hosted inference needs compute. The default local ranker has no model or API costs.
