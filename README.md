# Smart Study Partner

Smart Study Partner is a small Streamlit app that ranks learning-resource records for a topic. It combines each record's title, subject, description, and tags, converts that text to TF-IDF vectors, then orders records by cosine similarity to the learner's query.

> **Demo data:** `study_resources.csv` contains generated sample entries. It is useful for demonstrating search and ranking, but the entries are not verified courses and do not contain source URLs. Replace or enrich the CSV with reviewed, linkable resources before presenting the catalog as real learning material.

## What the app does

- Search for a topic, skill, or question using the main search box.
- Narrow results by subject, difficulty, and format.
- Choose how many results to show (1–20), with the strongest text matches first.
- Explore a subject from the home screen; selecting it runs a search.
- See each result's title, subject, level, format, description, tags, sample ID, and text-match score.
- Run a repeatable command-line category-ranking diagnostic with `python evaluate.py`.

The score indicates shared terms between the query and catalog entry. It is not a quality, trustworthiness, or learning-outcome rating. This version has no sign-in, learner history, saved lists, personalized learning path, or verified outbound resource links.

## Run locally

Requires Python 3.11 or newer and pip.

```powershell
cd SmartStudyPartner
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit (usually `http://localhost:8501`). The included CSV is ready to use. If it is missing, regenerate the deterministic 800-row sample catalog with:

```powershell
python generate_data.py
```

The same command works in macOS/Linux after activating `.venv` with `source .venv/bin/activate`.

## Deploy on Streamlit Community Cloud

The app is organized for Community Cloud: `app.py`, `requirements.txt`, and the CSV are at the repository root, with theme settings in `.streamlit/config.toml`. Community Cloud installs dependencies from the requirements file and runs the selected entrypoint from the repository root. See Streamlit's [file organization guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization) and [deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

1. Push this project to a GitHub repository. Keep `app.py`, `recommender.py`, `study_resources.csv`, `requirements.txt`, and `.streamlit/config.toml` committed.
2. Sign in at [share.streamlit.io](https://share.streamlit.io/) with GitHub and choose **Create app**.
3. Select the repository and deployment branch, then set **Main file path** to `app.py`.
4. Choose Python 3.11 for the app environment and deploy. The first build installs packages from `requirements.txt`.
5. Open the app URL and check search, all three filters, a category tile, and a query with no matches.

To update the deployed app, push changes to its connected branch. Community Cloud will rebuild when its source changes. Check the app's build logs if deployment fails, especially for missing files or dependency-install errors. Use a consistent Python version locally and in the deployment environment.

## How ranking works

```text
Learner query ──> same TF-IDF vocabulary ──> cosine similarity against catalog
                                                   │
CSV records ──> title + subject + description + tags
                                                   │
                                      apply selected filters
                                                   │
                                         highest scores first
```

The recommender loads the CSV once per app process, fits a `TfidfVectorizer` over record text, transforms each query, computes cosine similarity, removes zero-match rows, applies optional filters, and returns the requested number of ranked records. If there is no matching vocabulary, the app asks the learner to try a broader search.

## Evaluation

Run:

```bash
python evaluate.py
```

This samples up to 50 catalog rows with a fixed seed, builds queries from their tags, and reports category precision@5 and category hit rate@5. It is a reproducible diagnostic over generated sample data, not an independently labeled benchmark, user study, or validated accuracy claim. Do not use a percentage from this script as a production quality claim.

## Project files

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI, filters, search results, and category exploration |
| `recommender.py` | CSV validation and TF-IDF/cosine-similarity ranking |
| `study_resources.csv` | Included sample catalog (800 generated rows) |
| `generate_data.py` | Deterministic sample catalog generator |
| `evaluate.py` | Category-ranking diagnostic |
| `requirements.txt` | Python runtime dependencies |
| `.streamlit/config.toml` | App theme |
| `PROJECT_REQUIREMENTS.md` | Functional scope, UI specification, acceptance criteria, and production readiness |

## Production next steps

Before using this for real learners, curate actual resources and add their URLs, validate links and metadata, add a clear source/quality policy, and collect a labeled evaluation set. See [PROJECT_REQUIREMENTS.md](PROJECT_REQUIREMENTS.md) for the proposed requirements and acceptance criteria.
