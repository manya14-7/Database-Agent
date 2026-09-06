"""
Shared helper functions used by the function-calling and Assistants API
scripts. These functions are the only way the model is allowed to touch
the database — every query here is parameterized, so no user- or
model-supplied value is ever concatenated directly into SQL.
"""

import os
from sqlalchemy import create_engine, text

DB_PATH = os.getenv("DATABASE_PATH", "./db/test.db")
engine = create_engine(f"sqlite:///{DB_PATH}")


def get_hospitalized_increase_for_state_on_date(state_abbr: str, specific_date: str):
    """Return the reported hospitalization increase for a state on a given date."""
    query = text(
        """
        SELECT date, hospitalizedIncrease
        FROM all_states_history
        WHERE state = :state AND date = :date
        """
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"state": state_abbr, "date": specific_date}).fetchone()

    if result is None:
        return f"No hospitalization data found for {state_abbr} on {specific_date}."
    return {"date": result[0], "hospitalizedIncrease": result[1]}


def get_positive_cases_for_state_on_date(state_abbr: str, specific_date: str):
    """Return the reported positive case increase for a state on a given date."""
    query = text(
        """
        SELECT date, positiveIncrease
        FROM all_states_history
        WHERE state = :state AND date = :date
        """
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"state": state_abbr, "date": specific_date}).fetchone()

    if result is None:
        return f"No case data found for {state_abbr} on {specific_date}."
    return {"date": result[0], "positiveIncrease": result[1]}


# Tool/function schema shared by both the raw function-calling script
# and the Assistants API script.
tools_sql = [
    {
        "type": "function",
        "function": {
            "name": "get_hospitalized_increase_for_state_on_date",
            "description": "Get the number of new hospitalizations reported for a US state on a specific date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state_abbr": {
                        "type": "string",
                        "description": "Two-letter US state abbreviation, e.g. 'AK' for Alaska.",
                    },
                    "specific_date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format.",
                    },
                },
                "required": ["state_abbr", "specific_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_positive_cases_for_state_on_date",
            "description": "Get the number of new positive COVID-19 cases reported for a US state on a specific date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "state_abbr": {
                        "type": "string",
                        "description": "Two-letter US state abbreviation, e.g. 'AK' for Alaska.",
                    },
                    "specific_date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format.",
                    },
                },
                "required": ["state_abbr", "specific_date"],
            },
        },
    },
]
