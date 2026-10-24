from pathlib import Path
import os

from dotenv import load_dotenv


def main() -> None:
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path, override=False)

    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY is missing from the .env file.")

    os.environ.setdefault("GROQ_API_MODEL", "openai/gpt-oss-20b")
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGSMITH_PROJECT", "groq-chat-project")

    if not os.getenv("LANGSMITH_API_KEY"):
        raise ValueError("LANGSMITH_API_KEY is missing from the .env file.")

    from langchain_groq import ChatGroq

    llm = ChatGroq(
        model=os.getenv("GROQ_API_MODEL"),
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
    )

    response = llm.invoke("Hello, how are you?")
    print(response.content)


if __name__ == "__main__":
    main()
