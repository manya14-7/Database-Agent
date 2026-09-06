"""
Uses Azure OpenAI's function-calling feature to give the model access to
two specific, predefined functions instead of letting it write arbitrary
SQL. The model decides which function to call and with what arguments;
the actual database access happens entirely in helper.py, using
parameterized queries.
"""

import os
import sys
import json
from dotenv import load_dotenv
from openai import AzureOpenAI

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from helper import (
    tools_sql,
    get_hospitalized_increase_for_state_on_date,
    get_positive_cases_for_state_on_date,
)

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

AVAILABLE_FUNCTIONS = {
    "get_hospitalized_increase_for_state_on_date": get_hospitalized_increase_for_state_on_date,
    "get_positive_cases_for_state_on_date": get_positive_cases_for_state_on_date,
}


def ask(question: str):
    messages = [
        {
            "role": "system",
            "content": "You are an assistant that answers questions about a COVID-19 dataset.",
        },
        {"role": "user", "content": question},
    ]

    response = client.chat.completions.create(
        model="gpt-4-1106",
        messages=messages,
        tools=tools_sql,
        tool_choice="auto",
    )

    reply = response.choices[0].message

    # If the model didn't need a function, just return its answer.
    if not reply.tool_calls:
        return reply.content

    # Otherwise, run the requested function(s) and send the result back.
    messages.append(reply)

    for tool_call in reply.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        function_to_call = AVAILABLE_FUNCTIONS[function_name]
        function_response = function_to_call(**function_args)

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(function_response),
            }
        )

    final_response = client.chat.completions.create(
        model="gpt-4-1106",
        messages=messages,
    )
    return final_response.choices[0].message.content


def main():
    question = "How many hospitalized people did we have in Alaska on 2021-03-05?"
    print(ask(question))


if __name__ == "__main__":
    main()
