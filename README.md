# Hackathon Finder AI

Streamlit app for discovering hackathons through public web search. It filters editorial/guide pages and clear stale editions, normalizes tracking links, merges likely duplicates, and ranks using free local keyword and date rules. Optional Ollama summaries require a model installed on the machine running the app; the app works without it.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Windows PowerShell activation: `.venv\\Scripts\\Activate.ps1`.

## About a free built-in AI model

There is no reliable way to provide public, hosted LLM inference at $0 with no installation or server: model weights may be open-source, but serving them requires compute. This app therefore does not pretend a remote AI model is free. The default built-in search ranker runs locally as ordinary Python code without Ollama or model downloads. Optionally, run Ollama locally for AI-written relevance notes:

```bash
ollama pull qwen2.5:7b
ollama serve
```

Enable **Use optional local Ollama AI summaries**. If Ollama is not installed, running, or has no model, the app continues with local filtering and ranking.

## Search quality and limitations

Search queries explicitly target registration pages and exclude common guide/FAQ/recap terms. Results from guide/blog/archive paths and obvious retrospective or out-of-period editions are filtered. Tracking links are normalized and likely duplicate event titles are merged. Explicit dates are compared with the requested window; undated results are labeled unconfirmed. Search snippets can still be stale or wrong, so check the event's official page.

## Age-rule review

Every result offers the official page and age-rule evidence/review workflow. Extracted text is only a clue. Read the organizer's current rules and manually confirm eligibility; the app does not certify it.

## Tests

```bash
python -m unittest discover -s tests -v
```
