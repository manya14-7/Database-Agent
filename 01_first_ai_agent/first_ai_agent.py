"""
Basic sanity-check script for the Azure OpenAI connection.

This is the simplest possible use of the model — just sending a message
through LangChain and printing the response. Everything else in this
project builds on top of this connection.
"""

import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv()

model = AzureChatOpenAI(
    openai_api_version="2024-04-01-preview",
    azure_deployment="gpt-4-1106",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
)


def main():
    message = HumanMessage(
        content="Translate the sentence 'The weather is nice today' into French and Spanish."
    )
    response = model.invoke([message])
    print(response.content)


if __name__ == "__main__":
    main()
