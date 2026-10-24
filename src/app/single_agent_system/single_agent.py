import os
import certifi
import requests
from dotenv import load_dotenv
from pathlib import Path
from langchain.tools import tool
from langchain_tavily import TavilySearch
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain.agents import create_agent

os.environ["SSL_CERT_FILE"] = certifi.where()
env_file = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_file, override=False)

for key, value in {
    "GROQ_API_MODEL": "openai/gpt-oss-20b",
    "OPENAI_API_MODEL": "gpt-4o",
    "LANGSMITH_PROJECT": "groq-chat-project",
    "LANGSMITH_TRACING": "true",
}.items():
    os.environ.setdefault(key, value)


def get_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
    if value is None or not value.strip():
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
    model_name = os.getenv("OPENAI_API_MODEL", "gpt-4o")
    return ChatOpenAI(
        model_name=model_name,
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
def get_agent():
    tools = [get_weatherstack_tool, get_tavily_search_tool()]
    return create_agent(
        model=get_groq_llm(),
        tools=tools,
        system_prompt=(
            "You are a helpful assistant. "
            "You have a WeatherStack tool to search for weather information. "
            "You have a TavilySearch tool to search for information on the web."
        ),
    )


def agent_invoke(prompt: str) -> str:
    response = get_agent().invoke(
        {
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )
    return response["messages"][-1].content