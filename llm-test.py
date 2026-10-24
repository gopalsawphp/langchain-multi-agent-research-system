from pathlib import Path
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load .env from the same directory as this Python file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Validate Groq API key
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY is missing from the .env file.")

# Default model if not configured
if not os.getenv("GROQ_API_MODEL"):
    os.environ["GROQ_API_MODEL"] = "openai/gpt-oss-20b"

# Configure LangSmith tracing
os.environ.setdefault("LANGSMITH_TRACING", "true")
os.environ.setdefault("LANGSMITH_PROJECT", "groq-chat-project")

if not os.getenv("LANGSMITH_API_KEY"):
    raise ValueError("LANGSMITH_API_KEY is missing from the .env file.")

# Initialize Groq LLM with LangChain
llm = ChatGroq(
    model=os.getenv("GROQ_API_MODEL"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)

# Invoke the model; LangSmith traces this call automatically
response = llm.invoke("Hello, how are you?")

print(response.content)