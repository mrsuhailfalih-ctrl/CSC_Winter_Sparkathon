# Hackathon Finder AI

A no-paid-LLM Streamlit app for discovering hackathons through public web search. Results are deduplicated and ranked using a built-in local keyword/date ranker. Optional Ollama summaries run only when explicitly enabled and a model is available.

## Run the website locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Windows PowerShell activation: `.venv\\Scripts\\Activate.ps1`.

The app's search and ranking work without Ollama or a model download. The free DuckDuckGo search client can be rate-limited or unavailable because it relies on a public upstream service; it is not a guaranteed production search API. Existing hardware and internet access are assumed.

## Optional Ollama summaries

To enable local model summaries, install Ollama, then run:

```bash
ollama pull qwen2.5:7b
ollama serve
```

Enable **Use optional local Ollama AI summaries** in the app. If Ollama is stopped or the model is missing, the app explains the issue and continues with the local ranker. No request is made to Ollama unless the checkbox is enabled.

## Public deployment and cost

A public website can be hosted on a free app tier if available, but free tiers, sleep limits, and quotas change. The deployed app's built-in local ranker needs no model server. Ollama running on a developer's laptop is not reachable by public visitors; public Ollama inference requires a model server and compute, which cannot be guaranteed to be both free and reliably available. Do not expose Ollama's unauthenticated API publicly.

## Search and eligibility

The app removes obvious editorial pages, normalizes tracking links, merges likely duplicates, and prioritizes explicit date evidence and matching terms. Search snippets may be wrong or stale. Every result includes an official-page and age-rule evidence/review section. Extracted rules are clues only; a person must read the organizer's official rules and manually confirm eligibility.

## Tests

```bash
python -m unittest discover -s tests -v
```
