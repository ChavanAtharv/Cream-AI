# SchemeSaathi

Finding the right government scheme can be confusing. Information is spread across different websites, eligibility rules are not always easy to understand, and people may not know where to begin.

**SchemeSaathi** is being developed to make that process simpler. The idea is to give people one place to explore government schemes, understand who they are meant for, and learn what steps they may need to take next.

This project is being built as part of the **Sanjivani SJ-II** program. It is being developed incrementally, starting with a Python-based foundation and gradually adding data processing, exploration, and scheme discovery features.

## What we're trying to solve

People often miss out on schemes because they:

- Don't know which schemes are available to them.
- Find eligibility conditions difficult to interpret.
- Aren't sure what documents or steps are involved.
- Have to look through several sources to get a clear answer.

SchemeSaathi aims to make scheme-related information easier to find and understand.

## What the project is expected to offer

As development progresses, the project is intended to cover:

- **Scheme discovery** — browse or search for schemes based on a person's needs.
- **Eligibility guidance** — understand the basic conditions for a scheme.
- **Clear scheme details** — view benefits, requirements and other important information in one place.
- **Application guidance** — get a straightforward explanation of how to proceed.
- **Reliable references** — point users towards official sources so they can verify details.

The exact features will be shaped by the project requirements and implementation schedule.

## Current progress

Development is progressing according to the training schedule.

### Day 1 — Python foundation

- Created the initial project repository.
- Practised variables, user input and formatted output.
- Implemented a basic command-line menu.
- Used conditional statements and loops.

### Day 2 — Scheme records and CLI

- Created scheme records using Python dictionaries and lists.
- Implemented functions to load, search and retrieve scheme records.
- Added category-based counting.
- Created a command-line interface.
- Added unit tests using pytest.
- Set up a Python virtual environment and project dependencies.

### Day 3 — Data ingestion and exploration

- Collected the first real scheme record from the official myScheme portal.
- Added raw scheme data in JSON format.
- Implemented `app/ingest.py` to clean and normalize scheme records.
- Added error handling to skip invalid records.
- Generated `data/records.json` as the cleaned dataset.
- Created a pandas-based exploration script to examine scheme records.
- Added basic dataset statistics, including total schemes, ministry counts and missing values.

**Current dataset:** PM-KISAN is the first real scheme record. Some information, including the ministry field, is still pending verification.

This is an ongoing project, and additional schemes and functionality will be added as development progresses.

## Project structure

```text
SchemeSaathi/
│
├── analysis/
│   ├── __init__.py
│   └── explore.py
│
├── app/
│   ├── __init__.py
│   ├── cli.py
│   ├── ingest.py
│   └── records.py
│
├── data/
│   ├── raw/
│   │   └── pm_kisan.json
│   ├── records.json
│   └── sample_records.py
│
├── tests/
│   └── test_records.py
│
├── day01_intro.py
├── day01_menu.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Getting started

You'll need Python 3 installed.

### 1. Clone the repository

```bash
git clone https://github.com/ChavanAtharv/Cream-AI.git
cd Cream-AI
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run data ingestion

```bash
python -m app.ingest
```

### 5. Explore the dataset

```bash
python -m analysis.explore
```

### 6. Run tests

```bash
python -m pytest -v
```

## Data and information sources

Scheme information should be taken from dependable sources, preferably official government portals and scheme documentation.

The initial data collection uses:

- [myScheme — Government Schemes Portal](https://www.myscheme.gov.in/search)
- [PM-KISAN Scheme](https://www.myscheme.gov.in/schemes/pm-kisan)

Raw scheme information is stored separately from the cleaned dataset. This allows the ingestion process to validate and normalize records before they are used by the application.

Eligibility rules and application details can change, so users should always confirm the latest requirements with the relevant department or official portal before applying.

## Contributing

This project is being developed as part of the Sanjivani SJ-II schedule.

Keep changes focused, use clear commit messages, write tests where appropriate, and update this README when project functionality or setup instructions change.

## Note

SchemeSaathi is intended to help people understand available schemes and where to find official information. It does not replace advice or decisions from the government department responsible for a scheme.

## How to run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# start the API
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API docs.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service status and record count |
| GET | `/records?limit=` | List schemes (default 20, max 100) |
| GET | `/records/{id}` | One scheme by ID (404 if missing) |
| GET | `/search?q=` | Ranked search (TF-IDF + cosine similarity) |
| POST | `/questions` | Body `{"question": "..."}`; returns best-matching schemes |

Other commands:

```bash
python -m analysis.explore   # 3 facts about the records (pandas)
python -m pytest             # run the tests
```
