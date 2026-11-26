# Hackathon Finder AI

A Streamlit app that finds beginner-friendly hackathons from a local starter dataset, applies a basic age restriction filter, and optionally uses Ollama or Backboard for recommendation explanations.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Recommendation engines

### Local, $0 offline mode

No API key or external server is needed. It ranks the local dataset using interest keywords and explicit age fields.

### Ollama

Install Ollama and pull Qwen:

```bash
ollama pull qwen2.5:7b
ollama serve
```

Optional environment variables:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

Select **Ollama (local)** in the app.

### Backboard

Create a Backboard API key and choose an allowed provider/model. Add these values to a local `.env` file:

```text
BACKBOARD_API_KEY=your_key
BACKBOARD_LLM_PROVIDER=provider_name
BACKBOARD_MODEL_NAME=model_name
```

Backboard use may incur provider charges. The app's local mode remains free.

## Age restrictions

Age rules in `data/hackathons.json` are starter/example values except where a source is known. Some records intentionally have unknown eligibility. Unknown eligibility is never converted into a confirmed eligibility claim. Always verify rules on the official event page.

For minors, reviewers should confirm parental consent, privacy rules, and official eligibility requirements before participating.

## Privacy

The app stores neither exact age nor submitted preferences permanently. The exact age is sent only to the selected local or remote recommendation service.

## Safety warning

The app does not live-browse the web or guarantee current event information. Replace and verify the starter records before production use.
