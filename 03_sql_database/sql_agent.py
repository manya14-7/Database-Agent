"""
Loads the CSV dataset into a SQLite database and creates a LangChain SQL
agent that can translate natural-language questions into SQL, run them,
and explain the result.

The agent is explicitly instructed not to run destructive statements
(INSERT/UPDATE/DELETE/DROP) and to only touch the columns it actually
needs for a given question.
"""

import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_openai import AzureChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent

load_dotenv()

DATA_PATH = "./data/all-states-history.csv"
DB_PATH = os.getenv("DATABASE_PATH", "./db/test.db")

AGENT_PREFIX = """You are an assistant that answers questions about a COVID-19
dataset stored in a SQL database. Only use the columns and tables that are
relevant to the user's question. Always double-check your SQL query before
running it, and never execute INSERT, UPDATE, DELETE, or DROP statements.
Base your final answer strictly on the result returned by the query."""

AGENT_FORMAT_INSTRUCTIONS = """Use the following format:

Question: the input question you must answer
Thought: think about what data you need
Action: the action to take
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: the final answer to the original question"""

llm = AzureChatOpenAI(
    openai_api_version="2024-04-01-preview",
    azure_deployment="gpt-4-1106",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
)


def build_database():
    """Load the CSV into a fresh SQLite database (idempotent)."""
    engine = create_engine(f"sqlite:///{DB_PATH}")
    df = pd.read_csv(DATA_PATH).fillna(0)
    df.to_sql("all_states_history", con=engine, if_exists="replace", index=False)
    return engine


def build_agent():
    build_database()
    db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    return create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        prefix=AGENT_PREFIX,
        format_instructions=AGENT_FORMAT_INSTRUCTIONS,
        top_k=30,
        verbose=True,
    )


def main():
    agent = build_agent()
    question = """How many patients were hospitalized during October 2020
    in New York, and nationwide as the total across all states?
    Use the hospitalizedIncrease column."""
    result = agent.invoke(question)
    print(result)


if __name__ == "__main__":
    main()
