# Copyright (c) Microsoft. All rights reserved.

"""Weather Agent - Simple weather agent with mock data and time tools using Azure OpenAI."""

from datetime import datetime, timezone
from random import randint
from typing import Annotated

from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient
from pydantic import Field


def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Get the weather for a given location."""
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."


def get_time() -> str:
    """Get the current UTC time."""
    current_time = datetime.now(timezone.utc)
    return f"The current UTC time is {current_time.strftime('%Y-%m-%d %H:%M:%S')}."


# Module-level agent variable required by DevUI
# Uses Azure OpenAI with API key authentication
agent = ChatAgent(
    name="WeatherAgent",
    description="A helpful agent that provides weather information and current time",
    chat_client=AzureOpenAIChatClient(),
    instructions="You are a helpful assistant that can provide weather and time information.",
    tools=[get_weather, get_time],
)
