# Hackathon Finder

The app checks public event-hosting platform pages for structured event listings. It does not use DuckDuckGo, general-web result snippets, or AI-generated event discovery.

## Optional Momen AI ranking

Momen AI can rank candidate events after discovery. It does not find events or verify dates, eligibility, or registration details. The integration uses Momen's project GraphQL endpoint and your project's generated AI-agent mutation; exact field names and input variables depend on the AI agent configured in your Momen project.

1. In Momen, create/configure an AI agent and inspect its invocation mutation in the project's GraphiQL/schema tools.
2. Provide the GraphQL endpoint, the generated mutation operation, and its variables shape to the server configuration. The variables JSON may include the literal `{{PROMPT}}` wherever the prompt string should go. For example, a mutation declaring `$prompt: String!` uses `{"prompt":"{{PROMPT}}"}`; if your generated mutation expects an input object, configure a matching object shape instead.
3. Set these **server-side secrets only** in the hosting provider (for Streamlit, app Settings → Secrets):

```toml
MOMEN_GRAPHQL_URL = "https://villa.momen.app/zero/YOUR_PROJECT_ID/api/graphql-v2"
MOMEN_JWT = "YOUR_SERVER_SIDE_JWT"
MOMEN_AI_MUTATION = '''mutation Rank($prompt: String!) { yourGeneratedAgentOperation(prompt: $prompt) }'''
MOMEN_AI_VARIABLES_JSON = '{"prompt":"{{PROMPT}}"}'
```

The mutation and variables above are examples only—replace them with the exact operation and types from your Momen project. Keep credentials out of Git and browser code. Use a least-privilege token with appropriate expiry/rotation, and have an adult account owner review Momen's current age, privacy, quota, and billing rules before enabling it. Momen receives candidate titles, links, descriptions, dates, and locations for ranking. The integration rejects rankings for URLs not present in the candidate list and falls back without AI if configuration or requests fail.

The app is still hosted as Streamlit in this repository. Moving the entire UI/runtime to Momen would require creating/configuring a Momen project and rebuilding the interface there; it cannot be completed just by adding a Python API call.

## Event discovery

The app checks Devpost, Devfolio, MLH, Unstop, Eventbrite, and Luma public pages for structured event data. Some platforms render listings dynamically or limit automated access, so coverage is best-effort. No results does not mean no events exist. Verify each event on its official organizer page.

## Deploy and develop

Visitors need only the deployed app URL. Deployment should be managed by an account owner who meets the host's current requirements. For local development:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Tests: `python -m unittest discover -s tests -v`
