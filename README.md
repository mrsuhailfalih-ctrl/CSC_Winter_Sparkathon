# Hackathon Finder

The app checks public pages on Devpost, Devfolio, MLH, Unstop, Eventbrite, and Luma only—no DuckDuckGo or general web-result snippets.

## Momen AI web search

When configured, the app sends the search interests, other preferences, and date range to your Momen AI agent. The agent must have a web-search/browsing tool enabled and return JSON in this format:

```json
{"events":[{"url":"https://devpost.com/hackathons/example-event"}]}
```

The app accepts only HTTPS event routes on the allowlisted platform domains, fetches those pages itself, and displays page metadata rather than trusting AI-generated titles or dates. This reduces fabricated results but does not guarantee completeness or factual accuracy. If Momen is unavailable, the app falls back to checking the public platform pages directly. Momen tool/API usage may consume points or credits; review current pricing before enabling.

Configure the project's generated GraphQL mutation and server-side values in the hosting provider's secrets (never commit credentials):

```toml
MOMEN_GRAPHQL_URL = "https://villa.momen.app/zero/YOUR_PROJECT_ID/api/graphql-v2"
MOMEN_JWT = "YOUR_SERVER_SIDE_JWT"
MOMEN_AI_MUTATION = '''mutation Search($prompt: String!) { yourGeneratedAgentOperation(prompt: $prompt) }'''
MOMEN_AI_VARIABLES_JSON = '{"prompt":"{{PROMPT}}"}'
```

The mutation and variables are examples: use the exact operation, input shape, and output field from your Momen project's GraphiQL/schema. A GraphQL connection alone does not give a model web access; configure a web search/browsing tool for the agent in Momen. Keep tokens secret and have an adult account owner review Momen age, privacy, quota, and billing terms before use.

## Fallback source discovery

If Momen is not configured or its call fails, the app checks public platform listings directly and extracts event data when available. Sites that block automated access or render events dynamically can return no results; the app does not fall back to DuckDuckGo or general search.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Windows PowerShell activation: `.venv\\Scripts\\Activate.ps1`.

Tests: `python -m unittest discover -s tests -v`
