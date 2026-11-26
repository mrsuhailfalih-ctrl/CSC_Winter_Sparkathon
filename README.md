# Hackathon Finder AI

## Run

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Windows PowerShell activation: `.venv\\Scripts\\Activate.ps1`.

Search works without Ollama, an API key, or model weights. It uses public DuckDuckGo results, targets event platforms, removes directory/guide/past pages and deduplicates results. Search quality and availability are limited by the public search provider; verify all details with event organizers.

## Optional local AI summaries

The AI option uses Ollama's local HTTP API with Qwen 2.5 3B by default. To enable it, install Ollama on the same computer that runs Streamlit, then run:

```bash
ollama pull qwen2.5:3b
ollama serve
```

The app checks that Ollama is reachable and the model is installed before calling it, then uses `/api/chat` with JSON output. If unavailable, it displays a specific setup message and keeps showing results using deterministic local ranking. Configure `OLLAMA_MODEL` and `OLLAMA_BASE_URL` as environment variables if needed.

A public website cannot use Ollama on the visitor's laptop. Hosting a model for all website visitors requires server compute; no hosted inference is promised to be both reliable, effective, and free. Do not expose Ollama directly to the public internet.

## Result quality

Search queries target individual event URLs on Devpost, Devfolio, and Unstop plus general event-registration results. Generic directories (including `/hackathons` index pages), guide/news/archive pages, and stale editions are filtered. URL tracking parameters and likely duplicate event titles are normalized/merged. Dates are reported as evidence from snippets, never treated as official confirmation. An event page not matching known URL patterns may still appear, but every link must be verified manually.

Every result includes an official-page and age-rule review section. The age evidence extractor is only a clue; read the current organizer rules and manually confirm eligibility.

Tests: `python -m unittest discover -s tests -v`
