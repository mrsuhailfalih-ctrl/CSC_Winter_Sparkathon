# Hackathon Finder AI

A Streamlit prototype for finding hackathons from a local starter dataset, ranking matches locally or with Ollama, and optionally using Backboard.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Windows PowerShell activation: `.venv\\Scripts\\Activate.ps1`.

## Ollama (optional)

```bash
ollama pull qwen2.5:7b
ollama serve
```

Select **Ollama (local)** in the app. **Local (free/offline)** mode requires no model download or API key. Backboard is optional and may incur provider charges.

## Age-rule review workflow

1. Select an event with an official HTTPS URL and expand **Check age rule on the official page**.
2. Choose **Fetch age-rule evidence**. The app extracts text around age-related terms from the page.
3. Read the official page yourself; the extracted text is only a clue and may be incomplete, stale, or out of context.
4. Enter the age bounds stated by the official rules (or confirm that the official page explicitly says there is no age limit), then save your review.
5. The app compares your age with the rule you recorded.

This is human-confirmed evidence gathering, not automatic certification. Unknown rules remain unknown; they are not treated as proof that an event accepts every age. Reviews last only for the current Streamlit browser session. The checker only fetches public HTTPS HTML, caps response size, rejects private network destinations and cross-host redirects, and does not send the user's age to the event website.

## Dataset

`data/hackathons.json` is a starter dataset. Verify each event, source link, deadline, and eligibility rule before relying on or sharing it. Numeric age bounds should only be added to the dataset after checking an official source; set `age_rule_status` to `verified` and include the source and date you checked.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Privacy and limitations

The app does not persist entered age or review data. Page text can be dynamic or inaccessible to this lightweight HTML checker; in that case, open the official rules manually. This prototype does not guarantee current event details.
