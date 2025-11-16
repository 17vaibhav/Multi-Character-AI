# Multi-Character-AI

## Table of Contents

* [Overview](#overview)
* [Features](#features)
* [Project Structure](#project-structure)
* [Installation](#installation)
* [Environment Variables](#environment-variables)
* [Usage](#usage)

  * [Run the console agent (base_agent.py)](#run-the-console-agent-base_agentpy)
  * [Run the Streamlit app (app.py)](#run-the-streamlit-app-apppy)
* [How the Base Agent Works](#how-the-base-agent-works)
* [Streamlit App Details](#streamlit-app-details)
* [Character Profiles](#character-profiles)
* [Memory & State](#memory--state)
* [Requirements (example)](#requirements-example)
* [Development & Testing](#development--testing)
* [Troubleshooting](#troubleshooting)
* [Contributing](#contributing)
* [License](#license)

---

## Overview

This repository contains a small multi-character chat agent and a Streamlit-based UI. The base agent (`base_agent.py`) manages which fictional character the user is talking to and delegates generation to an LLM client. `app.py` provides a polished Streamlit front-end with per-character avatars, persistent session state, and a custom UI.

This project is useful as a demo or starting point for building persona-driven chatbots where multiple characters (each with a unique voice and memory) can be switched during a conversation.

## Features

* Switch between predefined characters (Yoda, Jar Jar Binks, Pikachu, Groot, Toge Inumaki).
* Preserve per-character conversation memory so each persona retains context.
* Asynchronous OpenAI client (`AsyncOpenAI`) for non-blocking requests.
* Console runner (`base_agent.py`) and Streamlit UI (`app.py`) with custom CSS and avatars.

## Project Structure

```
├── app.py                # Streamlit UI for multi-character chat
├── base_agent.py         # Console-based base agent managing characters & chat flow
├── requirements.txt      # Python dependencies (example provided below)
├── README.md             # This file
└── .env                  # Environment variables (not checked into VCS)
```

## Installation

1. Clone the repository:

```bash
git clone <your-repo-url>
cd <your-repo-directory>
```

2. Create and activate a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
# Windows (PowerShell or CMD): venv/Scripts/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt`, see the **Requirements (example)** section below for a minimal set.

## Environment Variables

Create a `.env` file in the project root with the following variable:

```
OPENAI_API_KEY=sk-...
```

Make sure `.env` is included in `.gitignore` to avoid leaking secrets.

## Usage

### Run the console agent (base_agent.py)

Start the interactive console agent:

```bash
python base_agent.py
```

Type messages in the terminal. To exit, type `exit` or `quit`.

### Run the Streamlit app (app.py)

Start the web UI using Streamlit:

```bash
streamlit run app.py
```

Open the printed local URL (usually `http://localhost:8501`) in your browser.

The Streamlit app provides:

* Sidebar with character cards and avatars.
* Chat window that renders conversation history from `st.session_state.chat_history`.
* An input box (via `st.chat_input`) to send messages which are processed asynchronously.

## How the Base Agent Works

High-level flow:

1. Load environment variables and initialize an asynchronous OpenAI client.
2. Maintain a `conversation_memory` dictionary keyed by character name.
3. If no active character, prompt the user to choose one.
4. For each user input, call `base_decision()` to decide: `stay`, `switch:<character>`, or `prompt`.
5. When chatting with a character, the agent sends the character system prompt and the previous conversation memory as context to the LLM.

### Important implementation notes

* The agent expects responses from `base_decision()` strictly in the form `switch:<name>`, `stay`, or `prompt`.
* Character names are matched against keys in the `CHARACTERS` dictionary; they are stored and referenced in lowercase.
* `chat_with_character()` appends both User and Character utterances to `conversation_memory` so context accumulates.

## Streamlit App Details

`app.py` implements a Streamlit-based UI with the following specifics:

* `CHARACTERS` contains `desc` (system prompt for the LLM) and `avatar` (emoji shown in the UI).
* Session state keys used:

  * `st.session_state.conversation_memory` — dict mapping character -> list of past utterances.
  * `st.session_state.active_character` — currently selected character (or `None`).
  * `st.session_state.chat_history` — list of `(speaker, text)` tuples rendered in the UI.
* UI styling uses injected CSS for chat bubbles and cards.
* The app uses `asyncio.run(process_user_input(user_input))` after collecting `st.chat_input`. Note: depending on your Streamlit/python environment, `asyncio.run()` may raise `RuntimeError` if Streamlit is already running an event loop. See Troubleshooting.

## Character Profiles

Each character has a concise persona prompt meant for the system role when calling the LLM. Example personas included:

* **Yoda** — Inverted, wise, calm.
* **Jar Jar Binks** — Silly, clumsy, cheerful.
* **Pikachu** — Speak only in variations of `Pika!`.
* **Groot** — Speak only `I am Groot` with tone variations.
* **Toge Inumaki** — Use onigiri ingredient words (short, token-like phrases).

You can extend or replace these by editing the `CHARACTERS` dictionary in `app.py` or `base_agent.py`.

## Memory & State

`conversation_memory` preserves messages per character for the lifetime of the process. This is stored in `st.session_state` for the Streamlit app. If you want persistent long-term memory across restarts, integrate a storage backend (file, database, or vector DB) and load/store memory on start/exit.

## Requirements (example)

A minimal `requirements.txt` for running the Streamlit app and base agent:

```
streamlit>=1.20.0
openai>=1.0.0
python-dotenv>=0.21.0
anyio>=3.0.0
```

If using a third-party AsyncOpenAI client library, ensure the correct package is installed. Adjust versions to match your environment.

## Development & Testing

* To iterate quickly, make sure your `.env` is configured.
* Consider mocking the LLM client in unit tests to avoid API calls and cost.
* To test switching behavior, craft unit tests for the `base_decision()` logic by simulating different `active_character` values and user messages.

## Troubleshooting

* **API key errors**: Ensure `OPENAI_API_KEY` is set and valid.
* **Streamlit + asyncio**: You may see `RuntimeError: asyncio.run() cannot be called from a running event loop` when using `asyncio.run()` inside Streamlit. Workarounds:

  * Use `anyio`/`trio` friendly calls (Streamlit is built on top of `anyio`).
  * Replace `asyncio.run(coro)` with `asyncio.get_event_loop().run_until_complete(coro)` after creating a new event loop:

    ```py
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(process_user_input(user_input))
    ```
  * Or refactor to use synchronous wrappers or background tasks supported by Streamlit.
* **Unexpected decision output**: If the LLM returns anything other than `switch:<name>`, `stay`, or `prompt`, sanitize and fallback to `prompt` or re-run the decision with a clarified prompt.

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`.
3. Commit your changes and open a PR describing the change.

Please follow code style and include unit tests where applicable.

## License

Add your license here (e.g., MIT, Apache-2.0). If unsure, add `LICENSE` file to the repo and reference it here.

---

If you'd like, I can:

* Generate a `requirements.txt` file in the repo and add it to the canvas.
* Add a small `run_streamlit.sh` helper script.
* Insert example `.env` and code snippets showing the expected shapes of LLM responses.

Tell me which you'd prefer and I will update the document accordingly.
