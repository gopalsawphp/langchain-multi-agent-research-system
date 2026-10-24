# LangChain Multi-Agent Research System

A Python project managed with [uv](https://docs.astral.sh/uv/) that includes a single-agent chat app and a multi-agent web research app.

GitHub repository: [gopalsawphp/langchain-multi-agent-research-system](https://github.com/gopalsawphp/langchain-multi-agent-research-system)

## Setup

Follow these steps from a terminal. The commands below use Windows PowerShell unless marked otherwise.

### 1. Install Python

Install **Python 3.13** from [python.org](https://www.python.org/downloads/). This project requires Python `>=3.13,<3.14`.

Check that Python is available:

```powershell
python --version
```

The version should be Python 3.13.x. If `python` is not recognized on Windows, enable it on your `PATH` or use the Python launcher, for example `py -3.13`.

### 2. Install Git and clone the project

Install Git from [git-scm.com](https://git-scm.com/downloads), then open a new terminal and verify it:

```powershell
git --version
```

Clone the repository and move into its folder:

```powershell
git clone https://github.com/gopalsawphp/langchain-multi-agent-research-system.git
cd langchain-multi-agent-research-system
```

### 3. Install uv

Install uv with pip:

```powershell
python -m pip install uv
```

Check the installation:

```powershell
uv --version
```

### 4. Initialize a project (only if needed)

This repository is already a uv project: it contains `pyproject.toml` and `uv.lock`. **When setting up this cloned repository, do not run `uv init`.**

Use `uv init project_name` only when starting a separate, new project:

```powershell
uv init project_name
cd project_name
```

### 5. Sync the project dependencies

From the cloned repository root (the folder containing `pyproject.toml`), run:

```powershell
uv sync
```

uv creates the project's `.venv` virtual environment if needed and installs the dependencies from the project configuration and lockfile.

### 6. Install packages and configure dependencies

The recommended installation method is `uv sync` from Step 5. Dependencies are declared in `pyproject.toml`, and `uv.lock` records their resolved versions so uv can reproduce the environment. When dependencies change, update the project configuration and run `uv lock` followed by `uv sync`.

For compatibility with pip, this repository also provides a pinned `requirements.txt`. To install packages with pip instead, create and activate a virtual environment, then run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS/Linux, activate that environment with `source .venv/bin/activate`. Choose either uv or pip to install dependencies; using `uv sync` is recommended for this project.

#### Configure API keys

Create a `.env` file in the repository root (next to `pyproject.toml`) and add your own keys:

```dotenv
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
WEATHERSTACK_API_KEY=your_weatherstack_api_key

# Optional: enable LangSmith tracing
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=groq-chat-project
```

The Multi-Agent Research System requires Groq and Tavily keys. The Single-Agent app also requires those keys for normal operation; WeatherStack is needed for weather requests. LangSmith tracing is optional. Keep `.env` private and do not commit API keys.

## Run the applications

Run these commands from the repository root. `uv run` uses the project's environment, so you do not need to activate `.venv` first.

### 7. Run the Single-Agent application

```powershell
uv run streamlit run single_agent.py
```

### 8. Run the Multi-Agent Research System

```powershell
uv run streamlit run multi_agent.py
```

Streamlit prints the local address to open in your browser (usually `http://localhost:8501`). Stop the running app with `Ctrl+C`. To run both apps at once, use separate terminals; Streamlit will choose another port for the second app.

## Project structure

```text
.
├── single_agent.py                # Single-Agent chat interface
├── multi_agent.py                 # Multi-Agent research interface
├── pyproject.toml                 # Project metadata and dependency declarations
├── uv.lock                        # Locked dependency versions for uv
├── requirements.txt               # Pinned requirements for pip users
└── src/app/
    ├── single_agent_system/       # Chat agent and tools
    └── multi_agent_research_system/
        ├── agents/                # Search, scraper, writer, and critic agents
        ├── pipelines/             # Research pipeline orchestration
        └── tools/                 # Web search and URL scraping tools
```
