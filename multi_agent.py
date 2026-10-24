
# --------------------------------------------------
# User Query Input + Pipeline Execution
# --------------------------------------------------
import json
import html
from datetime import datetime
from src.app.multi_agent_research_system.pipelines.pipeline import (
    run_research_pipeline,
)
import streamlit as st

st.markdown(
    '<div class="section-title">Start Your AI Research</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtext">
        Enter any question, choose a suggested topic, and run your
        multi-agent research pipeline on demand.
    </div>
    """,
    unsafe_allow_html=True,
)

# Initialize state
if "research_topic" not in st.session_state:
    st.session_state.research_topic = ""

if "research_result" not in st.session_state:
    st.session_state.research_result = None

if "research_time" not in st.session_state:
    st.session_state.research_time = None

# Optional suggested queries
st.markdown("**Try a sample query**")

samples = [
    "Impact of AI on the job market in 2026",
    "RAG vs fine-tuning for enterprise AI",
    "Future of AI agents in software engineering",
]

cols = st.columns(3)

for i, sample in enumerate(samples):
    with cols[i]:
        if st.button(sample, key=f"sample_{i}", use_container_width=True):
            st.session_state.research_topic = sample
            st.rerun()

# Query form: execution happens ONLY on submission
with st.form("research_query_form"):
    query = st.text_area(
        "Enter your research query",
        value=st.session_state.research_topic,
        height=120,
        placeholder=(
            "Example: How will AI agents change software development "
            "and employment in 2026?"
        ),
        help="Enter a specific question or topic for the research agents.",
    )

    execute = st.form_submit_button(
        "🚀 Execute Research Pipeline",
        use_container_width=True,
    )

# Execute the existing pipeline only after button submission
if execute:
    cleaned_query = query.strip()

    if not cleaned_query:
        st.warning("Please enter a research query first.")
    else:
        st.session_state.research_topic = cleaned_query
        st.session_state.research_result = None
        st.session_state.research_time = None

        try:
            with st.spinner(
                "🔍 Research agents are working on your query..."
            ):
                # Your existing pipeline; no hardcoded query
                result = run_research_pipeline(cleaned_query)

            st.session_state.research_result = result
            st.session_state.research_time = datetime.now().strftime(
                "%d %b %Y, %I:%M:%S %p"
            )

            st.success("Research pipeline executed successfully!")

        except Exception:
            # Log the full exception on the server in production.
            import logging

            logging.exception("Research pipeline execution failed")
            st.error(
                "Research execution failed. Please check your "
                "pipeline configuration and server logs."
            )

# --------------------------------------------------
# Display Results
# --------------------------------------------------
if st.session_state.research_result is not None:
    result = st.session_state.research_result

    st.divider()
    st.markdown(
        '<div class="section-title">📚 Research Output</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="result-header">
            <strong>Query:</strong>
            {html.escape(st.session_state.research_topic)}
            <br><br>
            <span style="color:#64748b;font-size:13px">
                Completed: {html.escape(st.session_state.research_time or "")}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if isinstance(result, (dict, list)):
        result_text = json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    else:
        result_text = str(result)

    tab1, tab2 = st.tabs(["📖 Research Results", "🧩 Raw Output"])

    with tab1:
        if isinstance(result, str):
            st.markdown(result)
        else:
            st.json(result)

    with tab2:
        st.code(result_text, language="text")

    st.download_button(
        "⬇️ Download Research",
        data=result_text,
        file_name="research_results.txt",
        mime="text/plain",
        use_container_width=True,
    )
