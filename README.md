# Personal Mechanic

A mobile-first Streamlit prototype that helps drivers make sense of a dashboard warning light. The driver answers a few questions and gets a clear urgency level, a plain-language explanation, a report to hand to a mechanic, and a list of nearby repair shops.

Built for the *Prototyping Products with AI* course (ESADE, Term 2), Assignments 1 and 2.

> **Disclaimer:** This is a prototype, not a certified diagnostic tool. Always consult a qualified mechanic, and stop driving if you feel unsafe.

## What it does

| Tab | Purpose |
|---|---|
| **Diagnose** | Collects the warning light type and behaviour (steady or flashing), symptoms, whether it appeared after refuelling, and an optional dashboard photo. |
| **Recommendation** | Shows the urgency (**Drive OK**, **Service Soon** or **Stop Now**), a confidence score, the top reasons and the next steps. With AI mode on, it adds a short explanation. |
| **Mechanic Report** | A structured summary of the case that the driver can download as `.txt` and share with a workshop. |
| **Find a Mechanic** | Finds nearby repair shops from OpenStreetMap, with distance, address, phone, opening hours and a map link. |
| **About** | In-app summary of the prototype and its limitations. |

### How the AI is used

The safety-critical decision is **rule-based and deterministic**. The LLM never changes the urgency. It is used only for language and for the mechanic search.

1. **Triage** ([logic/triage.py](logic/triage.py)) applies transparent rules to produce urgency, confidence, reasons and next steps. Examples are a flashing check-engine light, steam or overheating, and low oil pressure, all of which give *Stop Now*.
2. **Explanation and report** ([logic/llm.py](logic/llm.py)) is optional. OpenAI `gpt-4o-mini` rewrites the rule-based output into a calm explanation and a cleaner report.
3. **Mechanic finder** ([logic/mechanic_finder.py](logic/mechanic_finder.py)) uses LLM tool calling:
   - *LLM call 1* picks the search radius and priority through a `search_nearby_mechanics` tool call. The radius is 2 km for Stop Now, 5 km for Service Soon and 10 km for Drive OK.
   - The **Overpass API** (OpenStreetMap) returns real shops. It is free and needs no API key.
   - *LLM call 2* ranks the results and writes a short recommendation for the driver.

Without an API key, or with AI mode off, the app still works. Triage, the report and the mechanic search fall back to rules and a direct Overpass query.

## Project structure

```
.
├── app.py                    # Streamlit UI: sidebar, tabs, session state
├── logic/
│   ├── triage.py             # Rule-based urgency engine
│   ├── report.py             # Builds the plain-text mechanic report
│   ├── llm.py                # OpenAI: explanation + report polishing
│   └── mechanic_finder.py    # LLM tool use + Overpass API shop search
├── requirements.txt
└── README.md
```

## Getting started

**Requirements:** Python 3.10 or newer.

```bash
git clone https://github.com/smelkkk/personal-mechanic-streamlit-app.git
cd personal-mechanic-streamlit-app

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

streamlit run app.py
```

The app opens at http://localhost:8501.

### Enabling AI mode (optional)

AI features need an [OpenAI API key](https://platform.openai.com/api-keys). Set it as an environment variable **before** starting the app:

```bash
export OPENAI_API_KEY="sk-..."   # Windows PowerShell: $env:OPENAI_API_KEY="sk-..."
streamlit run app.py
```

Then switch on **AI explanations (LLM)** in the sidebar. Never commit your key. `.env` is git-ignored, but the app does not load `.env` files by itself, so use the environment variable.

## Usage walkthrough

1. Set the car model, mileage and whether you are driving in the sidebar.
2. In **Diagnose**, choose the warning type, light behaviour and symptoms, then click **Generate recommendation**.
3. Read the result in **Recommendation** and download the summary from **Mechanic Report**.
4. In **Find a Mechanic**, enter your latitude and longitude (defaults to Madrid) and click **Find mechanics**.

## Limitations

- Triage rules are simplified and cover a handful of warning types. They are not a substitute for professional diagnosis.
- The dashboard photo upload is not analysed yet. It is only recorded as attached.
- The warning type is chosen manually in the sidebar ("demo controls"). There is no automatic light recognition.
- Mechanic search uses raw coordinates, with no address geocoding. OpenStreetMap coverage varies by region, and the public Overpass endpoint may rate-limit or time out.
- AI output depends on `gpt-4o-mini` and needs an internet connection and a valid API key.

## Tech stack

Python · [Streamlit](https://streamlit.io) · [OpenAI API](https://platform.openai.com/docs) (chat completions and tool calling) · [Overpass API](https://overpass-api.de) / OpenStreetMap · `requests`

## Roadmap ideas

- Vision model to identify the warning light from the uploaded photo
- Address search (geocoding) instead of manual coordinates
- Live opening-hours filtering for "open now" shops
- Multi-language support
