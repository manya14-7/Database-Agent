"""
Runs the same function-calling logic through the Azure OpenAI Assistants
API instead of a single chat-completion call, using an assistant, a
thread, and a run. Also includes a separate example that uses the
built-in Code Interpreter tool on the raw CSV, for more open-ended
analytical questions.
"""

import os
import sys
import json
import time
from dotenv import load_dotenv
from openai import AzureOpenAI

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import helper
from helper import (
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


def wait_for_run(thread_id: str, run):
    """Poll a run until it finishes, handling any required tool calls along the way."""
    status = run.status
    start_time = time.time()

    while status not in ("completed", "cancelled", "expired", "failed"):
        time.sleep(2)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        status = run.status
        elapsed = int(time.time() - start_time)
        print(f"[{elapsed}s] run status: {status}")

        if status == "requires_action":
            tool_outputs = []
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                function_to_call = AVAILABLE_FUNCTIONS[function_name]
                function_response = function_to_call(**function_args)

                tool_outputs.append(
                    {"tool_call_id": tool_call.id, "output": str(function_response)}
                )

            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id, run_id=run.id, tool_outputs=tool_outputs
            )
            status = run.status

    return run


def ask_with_function_calling(question: str):
    assistant = client.beta.assistants.create(
        instructions="You are an assistant that answers questions about a COVID-19 dataset.",
        model="gpt-4-1106",
        tools=helper.tools_sql,
    )
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=question)

    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
    wait_for_run(thread.id, run)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value


def ask_with_code_interpreter(question: str, csv_path: str = "./data/all-states-history.csv"):
    uploaded_file = client.files.create(file=open(csv_path, "rb"), purpose="assistants")

    assistant = client.beta.assistants.create(
        instructions="You are an assistant that answers questions about a COVID-19 dataset.",
        model="gpt-4-1106",
        tools=[{"type": "code_interpreter"}],
        file_ids=[uploaded_file.id],
    )
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=question)

    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
    wait_for_run(thread.id, run)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value


def main():
    question = "How many hospitalized people did we have in Alaska on 2021-03-05?"
    print("--- Function calling via Assistants API ---")
    print(ask_with_function_calling(question))

    print("\n--- Code Interpreter ---")
    print(ask_with_code_interpreter(question))


if __name__ == "__main__":
    main()
