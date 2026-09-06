# Database Agent — Natural Language SQL Assistant

Most people who need an answer from a database don't actually want to write SQL — they just want to ask a question and get a straight answer. That's what this project does. It's an AI assistant that sits on top of structured data and lets you ask things in plain English, figures out how to get the answer, and replies in plain English too.

Under the hood it uses Azure OpenAI and LangChain to understand the question, and depending on the approach, either queries a Pandas DataFrame, generates and runs SQL against a SQLite database, or calls a predefined Python function that talks to the database directly. A COVID-19 state-level dataset is used as the sample data throughout, but the same approach would work with any structured dataset.

---

## Overview

Normally, getting an answer out of a database means knowing SQL and understanding the schema. This project removes that requirement.

You can just ask something like:

> "How many patients were hospitalized in New York during October 2020?"

and the agent works out what data it needs, goes and gets it, runs the right calculation, and gives you the answer — without you touching a query.

I built this in a few stages, starting with a basic LLM connection and gradually adding more structure and control: first a DataFrame agent, then a SQL agent, then function calling, and finally a version built on the Assistants API. Each stage solves the same problem in a slightly more reliable and controlled way.

---

## How It Works

```
                 User
                   │
        Natural-language question
                   │
                   ▼
             Azure OpenAI
                   │
   ┌───────────────┼────────────────┐
   │               │                │
   ▼               ▼                ▼
DataFrame       SQL Agent      Function Calling
  Agent             │                │
   │                ▼                ▼
   │           SQLite Database  Predefined Function
   │                │                │
   └────────────────┼────────────────┘
                     ▼
               Query Result
                     │
                     ▼
           Natural-language Answer
```

---

## Key Features

- Ask questions about structured data in plain English
- Azure OpenAI + LangChain integration
- Pandas DataFrame agent for quick CSV-based Q&A
- A LangChain SQL agent that writes and runs its own SQL
- SQLite database backend via SQLAlchemy
- Azure OpenAI function calling, using predefined functions instead of free-form DB access
- Assistants API workflow with threads, runs, and tool outputs
- Code Interpreter support for ad-hoc analysis on the raw dataset
- Guardrails that stop the agent from running destructive SQL

---

## Project Components

### 1. Azure OpenAI Connection
This is the base layer everything else builds on — a connection to an Azure OpenAI chat model that reads the user's question and figures out what kind of operation is actually needed.

```python
model = AzureChatOpenAI(
    openai_api_version="2024-04-01-preview",
    azure_deployment="gpt-4-1106",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)
```

### 2. CSV / DataFrame Agent
The COVID dataset is loaded into a Pandas DataFrame, and a LangChain agent sits on top of it so you can ask questions directly, no Pandas code required.

> "How many patients were hospitalized during July 2020 in Texas?"

This is the simplest version — good for quick exploration, but it doesn't scale well to large datasets or repeated production use.

### 3. SQL Database Agent
The same data also lives in a SQLite database. A LangChain SQL agent takes a natural-language question, writes the SQL for it, runs it, and explains the result back to you.

To keep this from going off the rails, the agent is instructed to:
- Only touch columns relevant to the question being asked
- Double-check a query before running it
- Never run `INSERT`, `UPDATE`, `DELETE`, or `DROP`
- Base its final answer strictly on the actual query result, not assumptions

### 4. Function Calling
Letting a model write arbitrary SQL is powerful but a little risky. So for a more controlled setup, specific Python functions are exposed to the model as callable tools instead:

```python
get_hospitalized_increase_for_state_on_date(state_abbr, specific_date)
get_positive_cases_for_state_on_date(state_abbr, specific_date)
```

Here's the flow:
1. The user asks a question
2. Azure OpenAI decides which function is relevant and works out the arguments
3. The application actually runs that Python function
4. The function runs a parameterized SQL query against SQLite
5. The result goes back to the model
6. The model turns it into a natural-language answer

The model never touches the database directly — it can only trigger functions that already exist, with arguments it extracted from the question. That's a meaningfully safer setup than letting it generate raw SQL.

### 5. Assistants API + Code Interpreter
The same functions are also wired into the Azure OpenAI Assistants API, using assistants, threads, messages, and runs instead of a single request/response call.

When the model realizes it needs data, the run pauses in a `requires_action` state. The app catches that, runs the right function, and feeds the result back in so the run can finish.

Separately, I also tried uploading the raw CSV to an assistant with Code Interpreter turned on. That lets it answer more open-ended analytical questions without needing a dedicated function for every possible query.

---

## Dataset

The project uses a COVID-19 state-level historical dataset with fields such as:

| Field | Description |
|---|---|
| `date` | Reporting date |
| `state` | US state abbreviation |
| `positive` | Cumulative positive cases |
| `positiveIncrease` | New positive cases that day |
| `hospitalized` | Cumulative hospitalizations |
| `hospitalizedIncrease` | New hospitalizations that day |
| `death` | Cumulative deaths |
| `deathIncrease` | New deaths that day |

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application language |
| Azure OpenAI | Language model backend |
| LangChain | Agent orchestration |
| Pandas | Data loading and manipulation |
| SQLite | Local relational database |
| SQLAlchemy | Database connectivity |
| OpenAI Assistants API | Function calling & tool execution workflow |
| NumPy | Numerical/data handling |
| JSON | Tool/function argument parsing |

---

## Project Structure

```
Database-Agent/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── 01_first_ai_agent/
│   └── first_ai_agent.py
│
├── 02_csv_data/
│   └── csv_agent.py
│
├── 03_sql_database/
│   └── sql_agent.py
│
├── 04_function_calling/
│   └── function_calling.py
│
├── 05_assistants_api/
│   └── database_assistant.py
│
├── data/
│   └── all-states-history.csv
│
├── db/
│   └── test.db
│
└── helper.py
```

---

## Getting Started

### 1. Clone the repository
```bash
git clone <your-repository-url>
cd Database-Agent
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your environment variables
Create a `.env` file in the root folder (and don't commit it) with:
```
AZURE_OPENAI_ENDPOINT=your-endpoint-here
AZURE_OPENAI_KEY=your-key-here
```

### 4. Run whichever version you want to try
```bash
python 01_first_ai_agent/first_ai_agent.py
python 02_csv_data/csv_agent.py
python 03_sql_database/sql_agent.py
python 04_function_calling/function_calling.py
python 05_assistants_api/database_assistant.py
```

---

## Example

Ask something like:

> "How many hospitalized people did Alaska have on 2021-03-05?"

The agent pulls out the state (`AK`) and the date, calls `get_hospitalized_increase_for_state_on_date`, pulls the value from SQLite, and hands you back a plain-English answer. No SQL required on your end.

---

## Design & Security Notes

A few things I did deliberately to keep this from being a database-access free-for-all:

- The SQL agent is explicitly told never to run `INSERT`, `UPDATE`, `DELETE`, or `DROP`
- Function-calling queries use parameterized SQL instead of string formatting, to avoid injection
- The agent only pulls the columns it actually needs for a given question
- API keys are kept out of the repo entirely and loaded from environment variables

If I were taking this further toward production, I'd also want to add proper authentication, input validation, query monitoring, and logging — none of that is in scope for a project like this, but it's the obvious next step.

---

## What I Learned

Building this taught me a lot about connecting LLMs to real, external systems instead of just generating text:

- How to connect an app to Azure OpenAI end to end
- Building and orchestrating agents with LangChain
- Letting an LLM reason over tabular data
- Translating natural language into SQL, and doing it safely
- Why function calling is a more controlled alternative to letting a model write arbitrary queries
- Working with the Assistants API — threads, runs, and tool outputs
- Using Code Interpreter for open-ended analysis on a dataset

---

## Future Improvements

- Build a simple web front-end instead of running scripts from the terminal
- Add authentication and role-based access to the database
- Expand the set of supported functions/queries
- Add memory so the agent can handle follow-up questions
- Wrap the whole thing in a FastAPI service
- Containerize with Docker
- Add proper logging and monitoring for the generated SQL

---

## Author

**Manya Agarwal**
Working on practical, LLM-powered applications and data-driven systems.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
