from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from src.app.multi_agent_research_system.multi_agent import get_groq_llm
from src.app.multi_agent_research_system.tools.tool import scrape_url, tavily_web_search_tool


# 1. First Agent: Research Agent
def build_search_agent():
    # Create the research agent using LangChain's create_agent function
    agent = create_agent(
        name="ResearchAgent",
        tools=[tavily_web_search_tool],
        model=get_groq_llm(),
        system_prompt=(
            "You are a research assistant. "
            "You have access to the TavilySearch tool to search for information on the web. "
        ),
    )
    return agent

# 2. Second Agent: Scraper Agent
def build_scraper_agent():
    # Create the scraper agent using LangChain's create_agent function
    agent = create_agent(
        name="ScraperAgent",
        tools=[scrape_url],
        model=get_groq_llm(),
        system_prompt=(
            "You are a web scraping assistant. "
            "You have access to the scrape_url tool to scrape content from web pages. "
        ),
    )
    return agent

writer_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are an expert content writer in a multi-agent research system.

        Your responsibilities:
        - Write a clear, accurate, and well-structured response.
        - Use the provided research content as the primary source.
        - Organize information with a suitable title and headings when useful.
        - Remove repetition and irrelevant details.
        - Do not invent facts or unsupported claims.
        - If the research content is insufficient, clearly state the limitation.
        - Return plain, readable Markdown.
        - Keep the final response within 300 words.

        The first call creates the initial report. On that call,
        "Previous Draft" and "Critic Feedback" are empty, and the previous
        score is "Not scored yet"; treat these as expected placeholders and
        write the report from the topic and research content without asking
        for missing revision information.
        On later calls, a previous draft, critic score, and critic feedback
        will be provided. Revise that draft to address the feedback, using the
        score to understand how much improvement is needed. Do not treat the
        score as a percentage of factual certainty.
        """
    ),
    (
        "human",
        """
        Write a details research report on the topic below based on the research content provided. Use the following format:
        
        topic:
        {topic}

        Research Content:
        {research_content}
        Structure the report as follows:
         - Introduction: Provide a brief overview of the topic.
        - Key findings should be highlighted in bullet points or numbered lists.
        - Conclusion: Summarize the main points and any implications or recommendations.
        - Sources(list all urls found in the research content) should be included at the end of the response.

        Previous Draft (if revising):
        {previous_writer_response}

        Previous Draft Critic Score:
        {previous_score}

        Critic Feedback (if revising):
        {revision_feedback}
         
        Write the final response based on the research content.
        When revising, use the previous draft's critic score as a percentage,
        address the critic's areas to improve, and preserve accurate information
        and the required structure.
        """
    ),
])

writer_agent = writer_prompt | get_groq_llm() | StrOutputParser()


critic_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are a strict content critic. Review the writer's response
        for accuracy, relevance, clarity, completeness, and word limit.
        Use the research content as evidence. Do not invent facts.
        Score from 0 to 10 and provide concise, actionable feedback.

        Output exactly:
        Score: X/10
        Strengths: [brief points]
        Areas to Improve: [brief points]
        Verdict: [one-line approval or revision recommendation]
        """
    ),
    (
        "human",
        """
        topic:
        {topic}

        Research Content:
        {research_content}

        Writer Response:
        {writer_response}
        """
    ),
])

critic_agent = critic_prompt | get_groq_llm() | StrOutputParser()