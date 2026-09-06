"""
Lets you ask natural-language questions directly against the raw CSV
dataset by wrapping it in a LangChain Pandas DataFrame agent.

Good for quick, ad-hoc exploration. Not meant to replace a real
database-backed agent for anything production-like — see
03_sql_database for that.
"""

import os
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

load_dotenv()

DATA_PATH = "./data/all-states-history.csv"

model = AzureChatOpenAI(
    openai_api_version="2024-04-01-preview",
    azure_deployment="gpt-4-1106",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
)


def build_agent():
    df = pd.read_csv(DATA_PATH).fillna(0)
    return create_pandas_dataframe_agent(
        llm=model,
        df=df,
        verbose=True,
        allow_dangerous_code=True,  # required by langchain-experimental for local, trusted CSVs only
    )


def main():
    agent = build_agent()
    question = "How many rows are in this dataset?"
    result = agent.invoke(question)
    print(result)


if __name__ == "__main__":
    main()
