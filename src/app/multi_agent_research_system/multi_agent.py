import os
import certifi
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

load_dotenv(dotenv_path=Path(__file__).resolve().parents[3] / ".env")

# Set the CA bundle path for HTTPS requests
os.environ["SSL_CERT_FILE"] = certifi.where()

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


def get_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"{var_name} is missing from the .env file.")
    return value

def get_groq_llm() -> ChatGroq:
    return ChatGroq(
        groq_api_key=get_env_variable("GROQ_API_KEY"),
        model=get_env_variable("GROQ_API_MODEL"),
        temperature=0,
    )

def get_openai_llm() -> ChatOpenAI:
    return ChatOpenAI(
        openai_api_key=get_env_variable("OPENAI_API_KEY"),
        model=get_env_variable("OPENAI_API_MODEL"),
        temperature=0,
    )
