# A2A Multi-Agent Search & Summarization Demo

A demonstration project implementing a **multi-agent system** for performing search and summarization tasks.
The application exposes a chat-style server where different agents collaborate to retrieve information and generate summaries.

The project is designed to showcase **agent-to-agent (A2A) interaction**, modular architecture, and scalable service deployment using Docker.

---

# Features

* Multi-agent architecture
* Search agent for retrieving information
* Summarization agent for condensing retrieved data
* Chat server interface
* Docker-based deployment
* Organized test structure (unit + integration)

---

# Project Structure

```
a2a-demo-multiagent-search-summarization
│
├── README.md
├── requirements.txt
├── docker-compose.yaml
├── dump.rdb
│
├── data/                # Dataset or cached information
├── docs/                # Documentation files
├── examples/            # Example scripts or usage demos
├── logs/                # Application logs
├── static/              # Static assets
│
├── src/
│   └── a2a_chat_server/
│       ├── __init__.py
│       ├── app.py                   # Main application entrypoint
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── search_agent.py      # Agent responsible for search
│       │   └── summarization_agent.py # Agent responsible for summarizing results
│       │
│       └── core/
│           └── __init__.py
│
└── tests/
    ├── __init__.py
    ├── integration/      # Integration tests
    └── unit/             # Unit tests
```

---

# Requirements

Python dependencies are defined in:

```
requirements.txt
```

Install them with:

```bash
pip install -r requirements.txt
```

Recommended environment:

* Python 3.9+
* pip
* Docker (optional)

---

# Setup Instructions

## 1. Clone the repository

```bash
git clone <repo-url>
cd a2a-demo-multiagent-search-summarization
```

## 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

Mac/Linux

```bash
venv\Scripts\activate
```

Windows

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

# Running the Application

Run the chat server:

```bash
python src/a2a_chat_server/app.py
```

The server will start and agents will be initialized for handling search and summarization requests.

---

# Running with Docker

If Docker is configured:

```bash
docker compose up --build
```

This will start the services defined in:

```
docker-compose.yaml
```

---

# Running Tests

Run all tests:

```bash
pytest
```

Run unit tests only:

```bash
pytest tests/unit
```

Run integration tests:

```bash
pytest tests/integration
```

---

# Agents Overview

### Search Agent

Responsible for retrieving relevant information from available sources.

File:

```
src/a2a_chat_server/agents/search_agent.py
```

### Summarization Agent

Processes search results and generates concise summaries.

File:

```
src/a2a_chat_server/agents/summarization_agent.py
```

---

# Logs

Application logs are stored in:

```
logs/
```

---
# .env
`
GOOGLE_API_KEY="your-api-key"
`
---
# Future Improvements

* Add more specialized agents
* Implement memory/context management
* Improve agent orchestration
* Add API documentation
* Add observability and tracing

---