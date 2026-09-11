"""Example A — The Weather Alert Worker.

The article's own example, built literally. The model gets two tools -
get_weather(city) and send_alert_email(to, subject, body) - and one
objective: check three cities, and email an alert if any of them crosses a
wind or storm threshold.

How many times the model calls get_weather (three, one per city - the
"unpredictable exact sequence" the article names, since it depends on how
the model chooses to sequence the checks), and whether it calls
send_alert_email at all, is NOT scripted here. That is the entire point of
this blueprint: the loop budget and tool allowlist are fixed in advance,
but the path through them is the model's decision, made turn by turn based
on what get_weather actually returns.

Chicago's fixture data (thunderstorm, 55 kph) should trigger an alert on
its own; London's 42 kph also clears the 40 kph threshold. Phoenix should
not. A well-behaved run therefore calls get_weather three times and
send_alert_email once, naming London and Chicago - but this script does not
hardcode that expectation, it just prints whatever the model actually did.

send_alert_email is SIMULATED: it prints what it would send and returns a
fake confirmation. No real email is ever sent by this chapter.
"""

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    WEATHER_DATA,
    banner,
    get_client,
    run_agent_loop,
    Tool,
)

GET_WEATHER_DECLARATION: dict[str, Any] = {
    "type": "function",
    "name": "get_weather",
    "description": (
        "Look up the current simulated weather conditions for one named city. "
        "Returns condition, wind_kph, and temp_c."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name, e.g. 'London', 'Phoenix', or 'Chicago'.",
            },
        },
        "required": ["city"],
    },
}

SEND_ALERT_EMAIL_DECLARATION: dict[str, Any] = {
    "type": "function",
    "name": "send_alert_email",
    "description": (
        "Send a weather-alert email. SIMULATED: never a real send, only a "
        "printed record and a fake confirmation."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Recipient address."},
            "subject": {"type": "string", "description": "Email subject line."},
            "body": {"type": "string", "description": "Plain-text email body."},
        },
        "required": ["to", "subject", "body"],
    },
}


def get_weather(city: str) -> dict[str, Any]:
    """Look up simulated weather data for `city` from WEATHER_DATA.

    Standing in for a real weather API call. Returns an "unknown city"
    payload rather than raising, so a model typo doesn't crash the loop -
    the model can see the error and recover.
    """
    data = WEATHER_DATA.get(city)
    if data is None:
        return {"error": f"no weather data for city={city!r}", "known_cities": list(WEATHER_DATA)}
    return {"city": city, **data}


def send_alert_email(to: str, subject: str, body: str) -> dict[str, Any]:
    """SIMULATED weather alert email — never a real send.

    Prints exactly what would have been sent, then returns a fake
    confirmation dict. Wiring this to a real mail provider is a deployment
    decision outside a teaching chapter's scope.
    """
    print("\n[SIMULATED EMAIL]")
    print(f"  to:      {to}")
    print(f"  subject: {subject}")
    print(f"  body:    {body}")
    return {
        "status": "simulated_send_ok",
        "to": to,
        "subject": subject,
        "note": "SIMULATED — no real email was sent.",
    }


def main() -> None:
    """Run the Weather Alert Worker loop to completion and print the transcript."""
    client = get_client()

    tools = [
        Tool(name="get_weather", declaration=GET_WEATHER_DECLARATION, fn=get_weather),
        Tool(
            name="send_alert_email",
            declaration=SEND_ALERT_EMAIL_DECLARATION,
            fn=send_alert_email,
            requires_review=True,
        ),
    ]

    objective = (
        "Check the weather in London, Phoenix, and Chicago. If any city has "
        "wind above 40 kph or a thunderstorm, send an alert email to "
        "ops@example.com summarizing which cities are affected and why."
    )

    banner("Example A — Weather Alert Worker")
    print(f"Objective: {objective}\n")

    result = run_agent_loop(client, objective, tools, max_turns=6)

    banner("Transcript")
    for step in result["transcript"]:
        turn = step["turn"]
        fc = step.get("function_call")
        fr = step.get("function_result")
        if fc is None:
            print(f"turn {turn}: no function_call — model considers itself done")
        else:
            print(f"turn {turn}: called {fc['name']}({fc['arguments']})")
            print(f"         -> result: {json.dumps(fr)}")

    banner("Final result")
    print(f"status: {result['status']}")
    if result["status"] == "done":
        print(f"answer:\n{result['answer']}")
    else:
        print("Loop hit MAX_TURNS before the model considered itself done — "
              "surfacing to a human rather than looping forever.")


if __name__ == "__main__":
    main()
