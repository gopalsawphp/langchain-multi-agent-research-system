import os
import certifi
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

load_dotenv(dotenv_path=Path(__file__).resolve().parents[3] / ".env", override=False)

# Set the CA bundle path for HTTPS requests
os.environ["SSL_CERT_FILE"] = certifi.where()

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
    return ChatGroq(
        groq_api_key=get_env_variable("GROQ_API_KEY"),
        model=os.getenv("GROQ_API_MODEL", "openai/gpt-oss-20b"),
        temperature=0,
    )


def get_openai_llm() -> ChatOpenAI:
    return ChatOpenAI(
        openai_api_key=get_env_variable("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_API_MODEL", "gpt-4o"),
        temperature=0,
    )
