import os
import certifi
import requests
from dotenv import load_dotenv
from pathlib import Path
from langchain.tools import tool
from langchain_tavily import TavilySearch
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_classic import hub
from langchain.agents import create_agent

os.environ["SSL_CERT_FILE"] = certifi.where()
env_file = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_file)

if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY is missing from the .env file.")

if not os.getenv("GROQ_API_MODEL"):
    os.environ["GROQ_API_MODEL"] = "openai/gpt-oss-20b"

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is missing from the .env file.")

if not os.getenv("OPENAI_API_MODEL"):
    os.environ["OPENAI_API_MODEL"] = "gpt-4o"

if not os.getenv("LANGSMITH_API_KEY"):
    raise ValueError("LANGSMITH_API_KEY is missing from the .env file.")

if not os.getenv("LANGSMITH_PROJECT"):
    os.environ["LANGSMITH_PROJECT"] = "groq-chat-project"

if not os.getenv("LANGSMITH_TRACING"):
    os.environ["LANGSMITH_TRACING"] = "true"

if not os.getenv("TAVILY_API_KEY"):
    raise ValueError("TAVILY_API_KEY is missing from the .env file.")

if not os.getenv("WEATHERSTACK_API_KEY"):
    raise ValueError("WEATHERSTACK_API_KEY is missing from the .env file.")

def get_env_variable(var_name:str) -> str:
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"{var_name} is missing from the .env file.")
    return value

def get_groq_llm() -> ChatGroq:
    api_key = get_env_variable("GROQ_API_KEY")
    model = os.getenv("GROQ_API_MODEL", "openai/gpt-oss-20b")
    return ChatGroq(
        model=model,
        api_key=api_key,
        temperature=0,
    )

def get_openai_llm() -> ChatOpenAI:
    api_key = get_env_variable("OPENAI_API_KEY")
    return ChatOpenAI(
        model_name="gpt-4o",
        openai_api_key=api_key,
        temperature=0,
    )

def get_tavily_search_tool() -> TavilySearch:
    return TavilySearch(
        tavily_api_key=get_env_variable("TAVILY_API_KEY"),
        max_results=3,
    )

@tool
def get_weatherstack_tool(city: str) -> str:
    """Fetches weather information for a given city using the Weatherstack API."""
    weatherstack_api_key = get_env_variable("WEATHERSTACK_API_KEY")
    res = requests.get(
        f"http://api.weatherstack.com/current?access_key={weatherstack_api_key}&query={city}"
    ).json()
    if "current" not in res:
        return f"Failed to retrieve weather information for {city}."
    return (
        f"City: {city}\n"
        f"Temperature: {res['current']['temperature']}°C\n"
        f"Weather: {res['current']['weather_descriptions'][0]}.\n"
        f"Humidity: {res['current']['humidity']}%\n"
        f"WindSpeed: {res['current']['wind_speed']} km/h\n"
    )
tools = [get_weatherstack_tool, get_tavily_search_tool()]
agent = create_agent(
    model=get_groq_llm(),
    tools=tools,
    system_prompt=(
        "You are a helpful assistant. "
        "You have a WeatherStack tool to search for weather information. "
        "You have a TavilySearch tool to search for information on the web."
    ),
)

def agent_invoke(prompt: str) -> str:
    response = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )
    return response["messages"][-1].content