from html import escape
from time import perf_counter

import pandas as pd
import streamlit as st

from recommender import StudyRecommender


st.set_page_config(
    page_title="Smart Study Partner",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def load_recommender():
    return StudyRecommender()


def choose_topic(topic):
    st.session_state["search_query"] = topic


def record_search_event(query, results, elapsed_ms, category_filter, level_filter, format_filter):
    """Keep lightweight, anonymous search telemetry for the current browser session."""
    events = st.session_state.setdefault("search_events", [])
    signature = (
        query.casefold(),
        category_filter or "",
        level_filter or "",
        format_filter or "",
    )
    if events and events[-1]["signature"] == signature:
        return

    events.append(
        {
            "signature": signature,
            "query": query,
            "result_count": len(results),
            "latency_ms": round(elapsed_ms, 2),
            "top_subject": results[0]["Category"] if results else "No match",
            "timestamp": pd.Timestamp.now().strftime("%H:%M:%S"),
        }
    )
    del events[:-100]


def render_live_analytics():
    """Render session-only metrics that update whenever a new search is performed."""
    events = st.session_state.get("search_events", [])
    if not events:
        return

    frame = pd.DataFrame(events)
    total_searches = len(frame)
    unique_queries = frame["query"].nunique()
    average_latency = frame["latency_ms"].mean()
    no_result_rate = (frame["result_count"].eq(0).mean()) * 100

    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    with st.expander("Live search insights", expanded=True):
        st.caption(
            "Updates in this browser session as you search. No queries are sent to an external analytics service."
        )
        metric_columns = st.columns(4)
        metric_columns[0].metric("Searches", total_searches)
        metric_columns[1].metric("Unique queries", unique_queries)
        metric_columns[2].metric("Avg. response", f"{average_latency:.0f} ms")
        metric_columns[3].metric("No-result rate", f"{no_result_rate:.0f}%")

        chart_columns = st.columns(2)
        with chart_columns[0]:
            st.markdown("**Most searched keywords**")
            query_counts = frame["query"].value_counts().head(8).rename("searches")
            st.bar_chart(query_counts)
        with chart_columns[1]:
            st.markdown("**Subjects returned by search**")
            subject_counts = (
                frame.loc[frame["top_subject"] != "No match", "top_subject"]
                .value_counts()
                .head(8)
                .rename("searches")
            )
            if subject_counts.empty:
                st.info("Search a broader topic to see subject trends.")
            else:
                st.bar_chart(subject_counts)

        recent = frame.loc[:, ["timestamp", "query", "result_count", "latency_ms", "top_subject"]].tail(10)
        st.dataframe(
            recent.iloc[::-1].rename(
                columns={
                    "timestamp": "Time",
                    "query": "Keyword",
                    "result_count": "Results",
                    "latency_ms": "Response (ms)",
                    "top_subject": "Top subject",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
        if st.button("Clear session insights", key="clear_search_insights"):
            st.session_state["search_events"] = []
            st.rerun()


def legacy_main():
    st.title("📚 Smart Study Partner")
    st.markdown("Find a useful starting point for your next learning goal.")
    st.caption(
        "This demo ranks sample catalog entries by text similarity. "
        "The catalog is generated sample data; entries are not verified course links."
    )

    try:
        recommender = load_recommender()
    except (FileNotFoundError, ValueError) as exc:
        st.error(f"Could not load the resource catalog: {exc}")
        st.info("From the project folder, run `python generate_data.py` and refresh this page.")
        st.stop()

    with st.sidebar:
        st.header("Refine results")
        categories = ["All categories"] + recommender.get_categories()
        selected_category = st.selectbox("Subject", categories)
        levels = ["All levels"] + recommender.get_levels()
        selected_level = st.selectbox("Difficulty", levels)
        formats = ["All formats"] + recommender.get_formats()
        selected_format = st.selectbox("Resource format", formats)
        num_results = st.slider("Results to show", min_value=1, max_value=20, value=5)
        st.divider()
        st.caption(
            f"{len(recommender.df):,} sample entries across "
            f"{len(recommender.get_categories())} subjects. Similarity is a text-match score, not a quality rating."
        )

    st.subheader("What do you want to learn?")
    st.text_input(
        "Enter a topic, skill, or question",
        placeholder="Try: Python data analysis with Pandas",
        key="search_query",
        label_visibility="collapsed",
    )

    query = st.session_state.get("search_query", "").strip()
    if query:
        st.subheader(f"Matches for “{query}”")
        category_filter = None if selected_category == "All categories" else selected_category
        level_filter = None if selected_level == "All levels" else selected_level
        format_filter = None if selected_format == "All formats" else selected_format
        results = recommender.recommend(
            query,
            top_n=num_results,
            category_filter=category_filter,
            level_filter=level_filter,
            format_filter=format_filter,
        )

        if not results:
            st.warning("No text matches found. Try a broader topic or change the filters.")
        else:
            st.caption(f"Showing {len(results)} ranked sample entries. Higher text-match scores mean more shared terms.")
            for result in results:
                with st.container(border=True):
                    title_col, score_col = st.columns([5, 1])
                    with title_col:
                        st.markdown(f"### {result['Title']}")
                    with score_col:
                        st.metric("Text match", f"{result['SimilarityScore']:.0%}")
                    st.caption(
                        f"{result['Category']}  ·  {result['Level']}  ·  {result['Format']}  ·  "
                        f"ID {result['Resource_ID']}"
                    )
                    st.write(result["Description"])
                    tags = [tag.strip() for tag in result["Tags"].split(",") if tag.strip()]
                    if tags:
                        st.caption("Topics: " + " · ".join(tags))
    else:
        st.info("Enter a topic above, or choose a subject to explore sample matches.")
        st.markdown("#### Explore subjects")
        for start in range(0, len(recommender.get_categories()), 4):
            category_row = recommender.get_categories()[start : start + 4]
            columns = st.columns(4)
            for column, category in zip(columns, category_row):
                with column:
                    st.button(
                        category,
                        key=f"category_{start}_{category}",
                        use_container_width=True,
                        on_click=choose_topic,
                        args=(category,),
                    )


def inject_styles():
    st.markdown(
        """
        <style>
        :root {
            --ink: #17283d;
            --ink-soft: #30435c;
            --blue: #2e63d6;
            --blue-deep: #214da9;
            --gold: #e8b84a;
            --paper: #f6f7f2;
            --white: #ffffff;
            --slate: #667383;
            --rule: #d9dee5;
            --mist: #eef1f5;
        }

        .stApp {
            background: var(--paper);
            color: var(--ink);
        }

        [data-testid="stAppViewContainer"] > .main {
            background:
                linear-gradient(90deg, rgba(46, 99, 214, 0.04) 1px, transparent 1px),
                var(--paper);
            background-size: 72px 72px;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        .block-container {
            max-width: 1320px;
            padding: 2.25rem 3.5rem 5rem;
        }

        [data-testid="stSidebar"] {
            background: var(--ink);
            border-right: 1px solid #2d405b;
        }

        [data-testid="stSidebar"] > div:first-child {
            padding: 2rem 1.45rem 1.5rem;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            color: #dce5f0 !important;
        }

        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            color: #aebed2 !important;
        }

        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: #213651;
            border-color: #50627a;
            color: #f6f7f2;
            border-radius: 2px;
        }

        [data-testid="stSidebar"] [data-baseweb="select"] div,
        [data-testid="stSidebar"] [data-baseweb="select"] input {
            color: #f6f7f2;
        }

        [data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"] {
            background: var(--gold);
            border-color: var(--gold);
        }

        [data-testid="stSidebar"] hr {
            border-color: #334965;
        }

        h1, h2, h3, p {
            color: var(--ink);
        }

        .app-brand {
            display: flex;
            align-items: center;
            gap: 0.65rem;
            margin-bottom: 3.6rem;
            color: var(--ink);
            font-size: 0.98rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        .brand-mark {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2rem;
            height: 2rem;
            border: 2px solid var(--ink);
            color: var(--blue);
            font-size: 0.9rem;
            font-weight: 800;
            line-height: 1;
        }

        .brand-note {
            margin-left: 0.3rem;
            color: var(--slate);
            font-size: 0.76rem;
            font-weight: 500;
        }

        .hero-copy {
            max-width: 830px;
            margin-bottom: 1.7rem;
        }

        .hero-copy h1 {
            max-width: 760px;
            margin: 0 0 0.8rem;
            color: var(--ink);
            font-size: clamp(2.8rem, 6vw, 5.7rem);
            font-weight: 760;
            letter-spacing: -0.075em;
            line-height: 0.95;
        }

        .hero-copy p {
            max-width: 600px;
            margin: 0;
            color: var(--ink-soft);
            font-size: 1.08rem;
            line-height: 1.55;
        }

        .demo-note {
            display: inline-flex;
            align-items: center;
            gap: 0.55rem;
            margin: 0 0 1.2rem;
            color: var(--slate);
            font-size: 0.78rem;
            line-height: 1.4;
        }

        .demo-note::before {
            content: "";
            display: inline-block;
            width: 0.55rem;
            height: 0.55rem;
            background: var(--gold);
            border-radius: 50%;
        }

        div[data-testid="stTextInput"] {
            max-width: 880px;
        }

        div[data-testid="stTextInput"] label {
            color: var(--ink);
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.01em;
        }

        div[data-testid="stTextInput"] input {
            min-height: 3.9rem;
            padding: 0.65rem 1.1rem;
            border: 2px solid var(--ink);
            border-radius: 2px;
            background: var(--white);
            box-shadow: 5px 5px 0 var(--gold);
            color: var(--ink);
            font-size: 1.08rem;
        }

        div[data-testid="stTextInput"] input:focus {
            border-color: var(--blue);
            box-shadow: 5px 5px 0 var(--blue);
        }

        .search-help {
            margin: 0.75rem 0 3.4rem;
            color: var(--slate);
            font-size: 0.82rem;
        }

        .section-rule {
            height: 1px;
            margin: 0 0 1.2rem;
            background: var(--rule);
        }

        .results-title {
            display: flex;
            flex-wrap: wrap;
            align-items: baseline;
            gap: 0.65rem;
            margin-bottom: 0.35rem;
            color: var(--slate);
            font-size: 0.9rem;
        }

        .results-title strong {
            max-width: 100%;
            overflow-wrap: anywhere;
            color: var(--ink);
            font-size: clamp(1.45rem, 2.5vw, 2.2rem);
            font-weight: 720;
            letter-spacing: -0.045em;
            line-height: 1.1;
        }

        .result-summary {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 0.8rem;
            margin-bottom: 1rem;
            color: var(--slate);
            font-size: 0.82rem;
        }

        .result-summary .active-filter {
            color: var(--blue-deep);
            font-weight: 700;
        }

        .result-row {
            display: grid;
            grid-template-columns: 3.1rem minmax(0, 1fr) 5.5rem;
            column-gap: 1.25rem;
            align-items: start;
            padding: 1.3rem 0.25rem 1.45rem 0;
            border-top: 1px solid var(--rule);
        }

        .result-row:last-child {
            border-bottom: 1px solid var(--rule);
        }

        .result-rank {
            padding-top: 0.15rem;
            color: var(--blue);
            font-size: 0.96rem;
            font-weight: 800;
            letter-spacing: 0.06em;
        }

        .result-content h3 {
            margin: 0 0 0.45rem;
            color: var(--ink);
            font-size: clamp(1.15rem, 2vw, 1.5rem);
            font-weight: 720;
            letter-spacing: -0.035em;
            line-height: 1.15;
        }

        .result-meta {
            margin-bottom: 0.7rem;
            color: var(--blue-deep);
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.01em;
        }

        .result-description {
            max-width: 760px;
            margin: 0 0 0.8rem;
            color: var(--ink-soft);
            font-size: 0.93rem;
            line-height: 1.55;
        }

        .result-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
        }

        .result-tag {
            padding: 0.25rem 0.48rem;
            background: var(--mist);
            color: var(--slate);
            font-size: 0.72rem;
            line-height: 1;
        }

        .result-score {
            padding-top: 0.08rem;
            text-align: right;
        }

        .result-score strong {
            display: block;
            color: var(--ink);
            font-size: 1.55rem;
            font-weight: 760;
            letter-spacing: -0.07em;
            line-height: 1;
        }

        .result-score span {
            display: block;
            margin-top: 0.35rem;
            color: var(--slate);
            font-size: 0.68rem;
            line-height: 1.2;
        }

        .explore-header {
            display: flex;
            flex-wrap: wrap;
            align-items: baseline;
            justify-content: space-between;
            gap: 0.75rem;
            margin-bottom: 1.05rem;
        }

        .explore-header h2 {
            margin: 0;
            color: var(--ink);
            font-size: 1.35rem;
            font-weight: 720;
            letter-spacing: -0.04em;
        }

        .explore-header p {
            max-width: 370px;
            margin: 0;
            color: var(--slate);
            font-size: 0.83rem;
            line-height: 1.45;
        }

        .empty-state {
            margin-top: 1.2rem;
            padding: 1.4rem 1.5rem;
            border-left: 4px solid var(--gold);
            background: var(--white);
        }

        .empty-state h2 {
            margin: 0 0 0.45rem;
            color: var(--ink);
            font-size: 1.15rem;
            letter-spacing: -0.02em;
        }

        .empty-state p {
            max-width: 620px;
            margin: 0;
            color: var(--ink-soft);
            font-size: 0.9rem;
            line-height: 1.5;
        }

        div[data-testid="stButton"] > button {
            min-height: 3rem;
            border: 1px solid var(--ink);
            border-radius: 2px;
            background: rgba(255, 255, 255, 0.52);
            color: var(--ink);
            font-weight: 650;
            text-align: left;
            transition: background 120ms ease, color 120ms ease, transform 120ms ease;
        }

        div[data-testid="stButton"] > button:hover {
            border-color: var(--blue);
            background: var(--blue);
            color: var(--white);
            transform: translateY(-2px);
        }

        div[data-testid="stButton"] > button:focus-visible {
            outline: 3px solid var(--gold);
            outline-offset: 2px;
        }

        .rail-brand {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            margin-bottom: 2.6rem;
            color: #f6f7f2;
            font-size: 1.05rem;
            font-weight: 750;
            letter-spacing: -0.025em;
        }

        .rail-brand-mark {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2rem;
            height: 2rem;
            border: 2px solid var(--gold);
            color: var(--gold);
            font-size: 0.9rem;
            line-height: 1;
        }

        .rail-lede {
            max-width: 220px;
            margin: 0 0 1.8rem;
            color: #aebed2 !important;
            font-size: 0.82rem;
            line-height: 1.5;
        }

        .rail-section-label {
            margin: 0 0 0.95rem;
            color: var(--gold);
            font-size: 0.82rem;
            font-weight: 750;
            letter-spacing: 0.01em;
        }

        .rail-facts {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.8rem;
            margin-top: 1.25rem;
            padding-top: 1.2rem;
            border-top: 1px solid #334965;
        }

        .rail-fact strong,
        .rail-fact span {
            display: block;
        }

        .rail-fact strong {
            color: #f6f7f2;
            font-size: 1.1rem;
            font-weight: 720;
        }

        .rail-fact span {
            margin-top: 0.2rem;
            color: #aebed2;
            font-size: 0.7rem;
            line-height: 1.25;
        }

        .rail-footnote {
            margin-top: 1.7rem;
            padding: 0.85rem 0.9rem;
            border-left: 2px solid var(--gold);
            background: #213651;
            color: #c5d1df !important;
            font-size: 0.74rem;
            line-height: 1.45;
        }

        @media (max-width: 900px) {
            .block-container {
                padding: 1.5rem 1.25rem 3.5rem;
            }

            .app-brand {
                margin-bottom: 2.6rem;
            }

            .hero-copy h1 {
                font-size: clamp(2.6rem, 12vw, 4.4rem);
            }

            .search-help {
                margin-bottom: 2.5rem;
            }
        }

        @media (max-width: 560px) {
            .result-row {
                grid-template-columns: 2.1rem minmax(0, 1fr);
                column-gap: 0.75rem;
            }

            .result-score {
                grid-column: 2;
                display: flex;
                align-items: baseline;
                gap: 0.4rem;
                padding-top: 0.7rem;
                text-align: left;
            }

            .result-score span {
                margin-top: 0;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                scroll-behavior: auto !important;
                transition-duration: 0.01ms !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_catalog_result(index, result):
    tags = [tag.strip() for tag in result["Tags"].split(",") if tag.strip()]
    tags_html = "".join(f'<span class="result-tag">{escape(tag)}</span>' for tag in tags)
    metadata = " / ".join(
        escape(value)
        for value in (result["Category"], result["Level"], result["Format"])
        if value
    )

    st.markdown(
        f"""
        <article class="result-row">
            <div class="result-rank">{index:02d}</div>
            <div class="result-content">
                <h3>{escape(result["Title"])}</h3>
                <div class="result-meta">{metadata} / ID {escape(result["Resource_ID"])}</div>
                <p class="result-description">{escape(result["Description"])}</p>
                <div class="result-tags">{tags_html}</div>
            </div>
            <div class="result-score">
                <strong>{result["SimilarityScore"]:.0%}</strong>
                <span>text match</span>
            </div>
        </article>
        """,
        unsafe_allow_html=True,
    )


def main():
    inject_styles()

    try:
        recommender = load_recommender()
    except (FileNotFoundError, ValueError) as exc:
        st.markdown(
            '<div class="app-brand"><span class="brand-mark">S</span>'
            '<span class="brand-name">Smart Study Partner</span></div>',
            unsafe_allow_html=True,
        )
        st.error(f"Could not load the resource catalog: {exc}")
        st.info("From the project folder, run python generate_data.py and refresh this page.")
        st.stop()

    categories = recommender.get_categories()
    levels = recommender.get_levels()
    formats = recommender.get_formats()

    with st.sidebar:
        st.markdown(
            '<div class="rail-brand"><span class="rail-brand-mark">S</span>'
            '<span>Smart Study Partner</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="rail-lede">A small catalog for finding the next useful thing to learn.</p>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="rail-section-label">Refine the list</div>', unsafe_allow_html=True)

        selected_category = st.selectbox("Subject", ["All subjects"] + categories)
        selected_level = st.selectbox("Difficulty", ["All levels"] + levels)
        selected_format = st.selectbox("Format", ["All formats"] + formats)
        num_results = st.slider("Results to show", min_value=1, max_value=20, value=5)

        st.markdown(
            f"""
            <div class="rail-facts">
                <div class="rail-fact"><strong>{len(recommender.df):,}</strong><span>sample entries</span></div>
                <div class="rail-fact"><strong>{len(categories)}</strong><span>subjects</span></div>
            </div>
            <div class="rail-footnote">
                This catalog is generated demo data. The score measures shared words,
                not source quality or learning outcomes.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="app-brand"><span class="brand-mark">S</span>'
        '<span class="brand-name">Smart Study Partner</span>'
        '<span class="brand-note">study catalog</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hero-copy"><h1>Find what to study next.</h1>'
        '<p>Describe a topic, skill, or question. The catalog will surface a few useful starting points.</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="demo-note">Generated sample catalog for demonstration; entries are not verified course links.</div>',
        unsafe_allow_html=True,
    )
    st.text_input(
        "Search the catalog",
        placeholder="Try: Python data analysis with Pandas",
        key="search_query",
    )
    st.markdown(
        '<div class="search-help">Use a subject, a concrete skill, or the question you would ask a tutor.</div>',
        unsafe_allow_html=True,
    )

    query = st.session_state.get("search_query", "").strip()
    category_filter = None if selected_category == "All subjects" else selected_category
    level_filter = None if selected_level == "All levels" else selected_level
    format_filter = None if selected_format == "All formats" else selected_format

    if query:
        search_started = perf_counter()
        results = recommender.recommend(
            query,
            top_n=num_results,
            category_filter=category_filter,
            level_filter=level_filter,
            format_filter=format_filter,
        )
        record_search_event(
            query,
            results,
            (perf_counter() - search_started) * 1000,
            category_filter,
            level_filter,
            format_filter,
        )

        st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="results-title"><span>Matches for</span>'
            f'<strong>{escape(query)}</strong></div>',
            unsafe_allow_html=True,
        )

        active_filters = sum(value is not None for value in (category_filter, level_filter, format_filter))
        filter_note = (
            f"{active_filters} filter{'s' if active_filters != 1 else ''} active"
            if active_filters
            else "All subjects, levels, and formats"
        )

        if not results:
            st.markdown(
                '<div class="empty-state"><h2>No starting points found.</h2>'
                '<p>Try a broader phrase, or clear one of the filters in the catalog rail. '
                'The ranking only returns entries that share words with your search.</p></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="result-summary"><span>Showing {len(results)} ranked sample entries.</span>'
                f'<span class="active-filter">{escape(filter_note)}</span></div>',
                unsafe_allow_html=True,
            )
            for index, result in enumerate(results, start=1):
                render_catalog_result(index, result)
    else:
        st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="explore-header"><h2>Start with a subject</h2>'
            '<p>Choose a lane and the search will begin with that subject.</p></div>',
            unsafe_allow_html=True,
        )

        for start in range(0, len(categories), 4):
            category_row = categories[start : start + 4]
            columns = st.columns(4)
            for column, category in zip(columns, category_row):
                with column:
                    st.button(
                        category,
                        key=f"catalog_category_{start}_{category}",
                        use_container_width=True,
                        on_click=choose_topic,
                        args=(category,),
                    )

    render_live_analytics()


if __name__ == "__main__":
    main()
