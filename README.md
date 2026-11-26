# Hackathon Finder AI

Streamlit app that performs live web search for hackathons, asks a locally hosted Ollama model to assess result relevance and date evidence, and provides an age-rule evidence/review section for every result.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
ollama pull qwen2.5:7b
ollama serve
```

In another terminal, run:

```bash
streamlit run app.py
```

Windows PowerShell activation: `.venv\\Scripts\\Activate.ps1`.

Set `OLLAMA_MODEL` and `OLLAMA_BASE_URL` in the environment if needed. Ollama and Qwen weights are free to run locally (hardware/internet are still required). The `ddgs` open-source client performs public DuckDuckGo web searches without an API key; availability/rate limits depend on the upstream service and can change. GitHub API keys are not used for web search.

## Search and AI behavior

- Enter interests, a requested date range, and extra details.
- The app searches live web results and shows their source URLs and snippets.
- Qwen/Ollama annotates the results using only the supplied search data. The app preserves URLs and never treats model output as verified facts.
- Search results are not guaranteed to be official, current, or complete. No numeric match score is shown.
- If Ollama is unavailable, live results still appear without AI annotations.

## Age-rule review

Every result includes an **Official page and age-rule review** section. The user can fetch possible age-related text from the source page, inspect it, and manually record age bounds after checking the official rules. Age comparison uses only the user's recorded rule. Unknown rules remain unknown; extracted text does not certify eligibility. Reviews are session-only.

The page checker only fetches public HTTPS HTML, caps response size, rejects private network destinations and cross-host redirects, and does not send the user's age to the event website. Dynamic pages may not expose readable text; check those rules manually.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Privacy and limitations

The user's age is not included in search queries. Search terms and additional details are sent to the public search provider. Ollama receives the result titles/snippets and preferences locally. Verify age rules, date, cost, deadlines, and registration on the event's official page.
