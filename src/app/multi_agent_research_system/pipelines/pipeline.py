
import json
import logging
import re
from typing import Any
from langchain_core.messages import AIMessage, ToolMessage
from src.app.multi_agent_research_system.agents.agent import (
    build_search_agent,
    build_scraper_agent,
    writer_agent,
    critic_agent,
)

logger = logging.getLogger(__name__)

# ==========================================
# Dynamic configuration: change anytime
# ==========================================
MAX_SEARCH_CHARS = 8_000
MAX_SCRAPER_INPUT_CHARS = 8_000
MAX_WRITER_INPUT_CHARS = 12_000
MAX_CRITIC_INPUT_CHARS = 10_000
MIN_ACCEPTABLE_CRITIC_SCORE = 8
MAX_WRITER_REVISIONS = 3


def get_agent_text(result: Any) -> str:
    """Normalize LangChain agent, LLM, and chain outputs to text."""

    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        messages = result.get("messages")

        if isinstance(messages, (list, tuple)):
            # Prefer the latest assistant message, not a tool result.
            for message in reversed(messages):
                if isinstance(message, AIMessage):
                    content = message.content

                    if isinstance(content, str) and content.strip():
                        return content

                    if content:
                        return json.dumps(
                            content,
                            ensure_ascii=False,
                            default=str,
                        )

            # Fallback for outputs containing only tool messages.
            for message in reversed(messages):
                if isinstance(message, ToolMessage):
                    content = message.content

                    if isinstance(content, str) and content.strip():
                        return content

            logger.warning(
                "No usable AIMessage found in agent output."
            )

        return json.dumps(
            result,
            ensure_ascii=False,
            default=str,
        )

    content = getattr(result, "content", None)

    if isinstance(content, str):
        return content

    if content is not None:
        return json.dumps(
            content,
            ensure_ascii=False,
            default=str,
        )

    logger.warning(
        "Unexpected agent output type: %s",
        type(result).__name__,
    )
    return str(result)


def get_critic_score(feedback: str) -> float | None:
    """Return the critic's score when it follows the expected format."""

    match = re.search(
        r"Score\s*:\s*(\d+(?:\.\d+)?)\s*/\s*10",
        feedback,
        re.IGNORECASE,
    )

    if not match:
        return None

    score = float(match.group(1))
    return score if 0 <= score <= 10 else None


def run_research_pipeline(topic: str) -> dict:
    """Run the multi-agent research pipeline for a user-supplied topic."""

    topic = topic.strip() if topic else ""

    if not topic:
        raise ValueError("Research topic cannot be empty.")

    state = {
        "topic": topic,
        "search_results": "",
        "scraped_content": "",
        "writer_response": "",
        "critic_feedback": "",
        "critic_score": None,
        "revision_count": 0,
        "status": "running",
        "failed_stage": None,
    }

    # ==========================================
    # STEP 1: SEARCH AGENT
    # ==========================================
    try:
        print("\n" + "=" * 50)
        print("Step 1 - Search Agent")
        print("=" * 50)

        search_agent = build_search_agent()

        search_result = search_agent.invoke({
            "messages": [
                (
                    "user",
                    f"""
Research topic: {topic}

Find up to 3 relevant, recent and reliable sources.

Requirements:
- Use the web search tool.
- Preserve each source's exact title and URL.
- Return the original search snippets.
- Do not invent sources, statistics or URLs.
- Clearly state if fewer than 3 useful results are found.
"""
                )
            ]
        })

        state["search_results"] = get_agent_text(search_result)

        if not state["search_results"].strip():
            raise RuntimeError("Search agent returned empty results.")

        state["search_results"] = state["search_results"][
            :MAX_SEARCH_CHARS
        ]

        print(state["search_results"])

    except Exception:
        state["failed_stage"] = "search"
        logger.exception("Search agent failed")
        state["status"] = "failed"
        raise

    # ==========================================
    # STEP 2: SCRAPER AGENT
    # ==========================================
    try:
        print("\n" + "=" * 50)
        print("Step 2 - Scraper Agent")
        print("=" * 50)

        scraper_agent = build_scraper_agent()

        scraper_result = scraper_agent.invoke({
            "messages": [
                (
                    "user",
                    f"""
Research topic: {topic}

Search results:
{state['search_results'][:MAX_SCRAPER_INPUT_CHARS]}

Instructions:
1. Extract up to 3 distinct HTTP/HTTPS source URLs from the
   search results above.
2. Call the scrape_url tool for each URL.
3. Use the actual extracted page content, not just search snippets.
4. Preserve the original URL and page title for every source.
5. Report scraping failures explicitly.
6. Never invent missing page content, facts, titles or citations.
7. Separate verified extracted content from failed sources.
8. Keep the combined extracted content concise for a free-tier LLM.
9. Return findings with their supporting source URLs.
"""
                )
            ]
        })

        state["scraped_content"] = get_agent_text(scraper_result)

        if not state["scraped_content"].strip():
            raise RuntimeError("Scraper agent returned empty content.")

        print(state["scraped_content"])

    except Exception:
        state["failed_stage"] = "scraper"
        logger.exception("Scraper agent failed")
        state["status"] = "failed"
        raise

    # ==========================================
    # STEP 3: WRITER AGENT
    # ==========================================
    try:
        print("\n" + "=" * 50)
        print("Step 3 - Writer Agent")
        print("=" * 50)

        research_combined = (
            f"RESEARCH TOPIC:\n{topic}\n\n"
            f"SEARCH RESULTS (discovery snippets only):\n"
            f"{state['search_results']}\n\n"
            f"SCRAPED SOURCE CONTENT:\n"
            f"{state['scraped_content']}"
        )

        research_combined = research_combined[:MAX_WRITER_INPUT_CHARS]

        writer_result = writer_agent.invoke({
            "topic": topic,
            "research_content": research_combined,
            "previous_writer_response": "",
            "previous_score": "Not scored yet",
            "revision_feedback": "",
        })

        state["writer_response"] = get_agent_text(writer_result)

        if not state["writer_response"].strip():
            raise RuntimeError("Writer agent returned empty content.")

        print(state["writer_response"])

    except Exception:
        state["failed_stage"] = "writer"
        logger.exception("Writer agent failed")
        state["status"] = "failed"
        raise

    # ==========================================
    # STEP 4: CRITIC AND WRITER REVISION LOOP
    # ==========================================
    try:
        print("\n" + "=" * 50)
        print("Step 4 - Critic and Writer Review")
        print("=" * 50)

        current_writer_response = state["writer_response"]
        best_writer_response = current_writer_response
        best_critic_feedback = ""
        best_critic_score = None
        revision_feedback = ""
        previous_score = "Not scored yet"

        for revision_number in range(MAX_WRITER_REVISIONS + 1):
            if revision_number > 0:
                try:
                    print(
                        f"\nWriter revision "
                        f"{revision_number}/{MAX_WRITER_REVISIONS}"
                    )
                    writer_result = writer_agent.invoke({
                        "topic": topic,
                        "research_content": research_combined,
                        "previous_writer_response": current_writer_response,
                        "previous_score": previous_score,
                        "revision_feedback": revision_feedback,
                    })
                    current_writer_response = get_agent_text(writer_result)

                    if not current_writer_response.strip():
                        raise RuntimeError(
                            "Writer agent returned empty content during revision."
                        )

                    state["revision_count"] = revision_number
                    print(current_writer_response)

                except Exception:
                    state["failed_stage"] = "writer"
                    logger.exception("Writer revision failed")
                    state["status"] = "failed"
                    raise

            critic_result = critic_agent.invoke({
                "topic": topic,
                "research_content": state["scraped_content"][
                    :MAX_CRITIC_INPUT_CHARS
                ],
                "writer_response": current_writer_response,
            })
            critic_feedback = get_agent_text(critic_result)
            critic_score = get_critic_score(critic_feedback)
            if critic_score is not None:
                previous_score = (
                    f"{critic_score:g}/10 ({critic_score * 10:g}%)"
                )

            print(critic_feedback)

            if critic_score is None:
                logger.warning(
                    "Critic feedback did not contain a valid score from 0 to 10; "
                    "stopping revisions."
                )
                if best_critic_score is None:
                    best_writer_response = current_writer_response
                    best_critic_feedback = critic_feedback
                break

            if best_critic_score is None or critic_score > best_critic_score:
                best_writer_response = current_writer_response
                best_critic_feedback = critic_feedback
                best_critic_score = critic_score

            if critic_score >= MIN_ACCEPTABLE_CRITIC_SCORE:
                break

            if revision_number < MAX_WRITER_REVISIONS:
                revision_feedback = critic_feedback

        state["writer_response"] = best_writer_response
        state["critic_feedback"] = best_critic_feedback
        state["critic_score"] = best_critic_score

    except Exception:
        if state["failed_stage"] is None:
            state["failed_stage"] = "critic"
            logger.exception("Critic agent failed")
            state["status"] = "failed"
        raise

    state["status"] = "success"

    print("\nResearch pipeline completed successfully.")

    return state
