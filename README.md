# LangChain Multi-Agent Research System

A Python application built with LangChain and managed with [uv](https://docs.astral.sh/uv/). It includes:

- A multi-agent research pipeline that searches the web, scrapes sources, writes a report, and reviews it.
- A Streamlit research interface.
- A separate Streamlit chat interface with web search and weather tools.

## Repository

GitHub: [gopalsawphp/langchain-multi-agent-research-system](https://github.com/gopalsawphp/langchain-multi-agent-research-system)

Clone URL:

```text
https://github.com/gopalsawphp/langchain-multi-agent-research-system.git
```

## Requirements

- Python **3.13** (the project requires `>=3.13,<3.14`).
- uv.
- API keys for the services you plan to use:
  - **Groq** and **Tavily** are needed for the research pipeline.
  - **Groq**, **Tavily**, and **WeatherStack** are needed for all capabilities in the chat app. WeatherStack is only called for weather requests.
  - LangSmith tracing and OpenAI are optional; the app uses Groq as its configured model.

## Setup

### 1. Install Python

Install Python 3.13 from [python.org](https://www.python.org/downloads/) and verify it is available in your terminal:

```powershell
python --version
```

The output should report Python 3.13.x. If `python` is not recognized on Windows, enable Python on your `PATH` or use the Python launcher (`py -3.13`).

### 2. Install uv

In PowerShell, run the official Windows installer:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Open a new terminal if needed, then check the installation:

```powershell
uv --version
```

For macOS/Linux, see the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

### 3. Clone the repository

```powershell
git clone https://github.com/gopalsawphp/langchain-multi-agent-research-system.git
cd langchain-multi-agent-research-system
```

### 4. Sync the project dependencies

This repository is already configured as a uv project: `pyproject.toml` defines its dependencies and Python version, and `uv.lock` locks dependency versions. You do **not** need to run `uv init` after cloning; `uv init` is for creating a new project and is not needed to set up this one.

Install the project and its dependencies:

```powershell
uv sync
```

`uv sync` creates the project `.venv` environment if it does not exist and installs the locked dependencies.

### 5. Activate the virtual environment

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can skip activation and prefix the following commands with `uv run`, for example `uv run streamlit run multi_agent.py`.

Command Prompt:

```bat
.venv\Scripts\activate.bat
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 6. Configure API keys

Create a `.env` file in the repository root (the same folder as `pyproject.toml`) and add your own provider keys:

```dotenv
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
WEATHERSTACK_API_KEY=your_weatherstack_api_key

# Optional: enable LangSmith tracing
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=groq-chat-project
```

The multi-agent research pipeline needs `GROQ_API_KEY` and `TAVILY_API_KEY`. The single-agent chat uses `WEATHERSTACK_API_KEY` when you request weather. Keep `.env` private; do not commit API keys. `.env` is excluded by `.gitignore`.

## Run the project

Run commands from the repository root with the virtual environment activated. Alternatively, use `uv run <command>` without activating it.

### Option 1: Run a pipeline or chat request with Python

There is no standalone command-line prompt loop. Call the Python functions directly; these examples execute one request and print the response.

Run a research query:

```powershell
python -c "from src.app.multi_agent_research_system.pipelines.pipeline import run_research_pipeline; result = run_research_pipeline('How are AI agents changing software engineering?'); print(result['writer_response'])"
```

Run a single-agent chat request:

```powershell
python -c "from src.app.single_agent_system.single_agent import agent_invoke; print(agent_invoke('What is LangChain?'))"
```

You can also use `uv run python -c "..."` in place of `python -c "..."`.

### Option 2: Run a Streamlit app

Start the multi-agent research interface:

```powershell
streamlit run multi_agent.py
```

Or start the single-agent chat interface:

```powershell
streamlit run single_agent.py
```

Streamlit prints a local URL (usually `http://localhost:8501`) to open in your browser. Stop the server with `Ctrl+C`.

If you did not activate the environment, use:

```powershell
uv run streamlit run multi_agent.py
```

Replace `multi_agent.py` with `single_agent.py` to launch the chat interface instead.

## Project layout

```text
.
├── multi_agent.py                 # Multi-agent research UI
├── single_agent.py                # Single-agent chat UI
├── src/app/
│   ├── multi_agent_research_system/
│   │   ├── agents/                # Search, scraping, writing, and critic agents
│   │   ├── pipelines/             # Research pipeline orchestration
│   │   └── tools/                 # Web search and URL scraping tools
│   └── single_agent_system/       # Chat agent and tools
├── pyproject.toml                 # Project metadata and dependencies
└── uv.lock                        # Locked dependency versions
```
