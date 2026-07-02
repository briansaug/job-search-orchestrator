"""Thin wrappers around the Anthropic SDK.

Three call shapes, matching the three things agents in this system do:
  ask()             — plain text in, text out
  ask_structured()  — force a JSON-schema-valid dict back (no parsing guesswork)
  ask_with_search() — give the model the web_search server tool and let it
                      research before answering

Claude 5 note: Sonnet 5 runs adaptive thinking by default and thinking
bills into max_tokens, so the defaults below carry headroom.
"""

import json

import anthropic

from .config import MODEL

_client = anthropic.Anthropic()


def ask(prompt: str, system: str = "", max_tokens: int = 8192) -> str:
    response = _client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system or anthropic.NOT_GIVEN,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in response.content if b.type == "text")


def ask_structured(prompt: str, schema: dict, system: str = "", max_tokens: int = 8192) -> dict:
    """Constrain the response to a JSON schema via output_config.format."""
    response = _client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system or anthropic.NOT_GIVEN,
        output_config={"format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": prompt}],
    )
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def ask_with_search(prompt: str, system: str = "", max_searches: int = 8,
                    max_tokens: int = 16384) -> str:
    """Server-side web search: the model issues queries, Anthropic runs them.

    Handles the pause_turn stop reason — the server-side tool loop caps at
    10 iterations per request and asks us to re-send to continue.
    """
    messages = [{"role": "user", "content": prompt}]
    tools = [{"type": "web_search_20260209", "name": "web_search",
              "max_uses": max_searches}]

    for _ in range(5):  # continuation cap so a stuck loop can't run forever
        response = _client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system or anthropic.NOT_GIVEN,
            tools=tools,
            messages=messages,
        )
        if response.stop_reason == "pause_turn":
            messages = [messages[0],
                        {"role": "assistant", "content": response.content}]
            continue
        break

    return "".join(b.text for b in response.content if b.type == "text")
