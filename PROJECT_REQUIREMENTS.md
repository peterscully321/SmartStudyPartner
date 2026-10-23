# Smart Study Partner — project requirements

## 1. Purpose

Help a learner find relevant starting material by entering a subject, skill, or question. The deployed MVP demonstrates text-based ranking over a small catalog. The current CSV is synthetic demo data, so this deployment is a recommendation-system demo, not a directory of verified courses.

## 2. Users and primary journey

**Primary user:** a learner who knows what they want to study but needs a few relevant starting points.

1. The learner opens the app and sees a clear search prompt plus sample subject shortcuts.
2. They enter a topic or pick a subject.
3. They optionally filter by subject, difficulty, or format and choose a result count.
4. The app presents the highest-scoring matching entries first.
5. The learner uses title, description, tags, and metadata to decide whether an entry is relevant.

For a production catalog, step 5 must include a verified source name and working resource URL; those fields are not present in the current dataset.

## 3. Functional requirements

| ID | Requirement | MVP status |
|---|---|---|
| FR-01 | Load a local CSV catalog containing resource ID, title, category, description, level, format, and tags. Show a useful error if the file or required fields are missing. | Implemented |
| FR-02 | Accept a free-text search and rank entries by TF-IDF cosine similarity. | Implemented |
| FR-03 | Exclude entries with zero text similarity and show a helpful empty state. | Implemented |
| FR-04 | Filter ranked entries by category, level, and format without changing the scoring method. | Implemented |
| FR-05 | Let the learner choose a result count from 1 to 20. | Implemented |
| FR-06 | Show each result's title, description, category, level, format, tags, ID, and similarity score. | Implemented |
| FR-07 | Make category shortcuts populate the search and trigger results. | Implemented |
| FR-08 | Explain that scores measure text similarity, not source quality or educational outcomes. | Implemented |
| FR-09 | Provide a deterministic sample-data generator and repeatable diagnostic evaluation script. | Implemented |
| FR-10 | Provide real, reviewed learning resources with working URLs and visible attribution. | Required before production; not implemented |
| FR-11 | Let learners save resources or resume a prior search across sessions. | Future enhancement; not implemented |
| FR-12 | Provide personalization based on goals, experience, or learning history. | Future enhancement; not implemented |

## 4. UI and interaction requirements

- **Page structure:** product name and one-line purpose at the top; primary search field in the main area; refinement controls in the sidebar; results below the search.
- **Search:** support a phrase such as “Python data analysis with Pandas.” Searching updates results; category shortcuts start a search with that subject.
- **Filters:** provide “All” defaults for subject, difficulty, and format. Changing filters should be reversible and should not hide the active query.
- **Result card:** make the title the strongest element; place the text-match percentage beside it; show subject, difficulty, and format as compact metadata; show a short description and topic tags beneath.
- **Home state:** when no query exists, invite a search and show clickable subject shortcuts.
- **No-results state:** say that no text matches were found and suggest a broader query or clearing filters.
- **Catalog error state:** explain which catalog problem occurred and how to restore/regenerate the CSV.
- **Small screens:** content should stack naturally; controls must remain readable and usable without horizontal scrolling.
- **Trust:** label the included catalog as generated sample data and avoid presenting synthetic entries as verified external courses.

## 5. Output contract

Each recommendation is a catalog row with `Resource_ID`, `Title`, `Category`, `Description`, `Level`, `Format`, `Tags`, and a calculated `SimilarityScore` from 0 to 1. The UI renders the score as a percentage. Scores are query-relative text overlap; they are not probabilities, relevance guarantees, or quality ratings. The MVP has no URL field, so it cannot direct learners to a course page.

## 6. Core system behavior

1. Read and validate the CSV at app startup.
2. Join title, category, description, and tags into the text used for ranking.
3. Fit a TF-IDF vectorizer on the catalog text.
4. Transform a learner query with the same vocabulary.
5. Compute cosine similarity between the query vector and each resource vector.
6. Apply the selected category, level, and format filters; omit zero-score rows; return up to the requested count in descending score order.

The CSV and model are in memory for the running process. There is no database, account system, event tracking, or external AI service in the MVP.

## 7. Non-functional requirements

- **Deployability:** run with Python 3.11+ and dependencies declared in `requirements.txt`; all runtime files must be committed alongside `app.py`.
- **Determinism:** the sample generator and evaluation sampling use fixed seeds by default; equal similarity scores preserve catalog order.
- **Failure handling:** missing or malformed catalogs should produce a clear UI message rather than an unhandled traceback.
- **Privacy:** search queries are processed in memory and are not saved by this application.
- **Maintainability:** keep presentation (`app.py`), ranking/data validation (`recommender.py`), data generation, and diagnostic evaluation separate.
- **Accessibility:** use descriptive labels, readable contrast, meaningful empty/error states, and keyboard-operable standard Streamlit widgets.

## 8. Acceptance criteria for the deployable demo

- `streamlit run app.py` starts from the repository root with the checked-in CSV.
- A topic query returns ranked sample entries with metadata and scores.
- Subject, difficulty, format, and result-count controls affect displayed results.
- Subject shortcuts populate a query and return matches.
- A query with only out-of-vocabulary terms produces the no-results state.
- A missing CSV or missing required column produces an explanatory error.
- `python generate_data.py` creates 800 repeatable sample rows.
- `python evaluate.py` prints measured category diagnostic metrics and no hard-coded target score.
- The page clearly identifies that the catalog is generated demonstration content.

## 9. Deployment and release checklist

1. Commit `app.py`, `recommender.py`, `study_resources.csv`, `requirements.txt`, and `.streamlit/config.toml` to the GitHub repository.
2. Create a Streamlit Community Cloud app from that repository and set the entrypoint to `app.py`.
3. Use Python 3.11 for the deployed environment and keep the local environment aligned.
4. Confirm the app builds, loads the CSV, and supports a normal query, each filter, a category shortcut, and a no-match query.
5. For production use, replace demo data with reviewed resources, add a required `URL` and source/last-checked metadata, validate links, and update the card to make the title a clickable link.
6. Create a labeled offline evaluation set and report its method and results accurately before making quality claims.

## 10. Suggested production roadmap

1. **Verified catalog:** real materials, working URLs, source attribution, freshness checks, and an editorial review workflow.
2. **Better relevance:** evaluate against human-labeled queries; use synonyms or semantic embeddings only if they improve those measured results.
3. **Learner features:** save/share results and optional preferences, with explicit consent and a clear retention policy.
4. **Operations:** monitor app health and broken links; add authentication only if the product needs private or personalized learner data.
