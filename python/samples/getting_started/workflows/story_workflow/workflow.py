# Copyright (c) Microsoft. All rights reserved.

"""Interactive Story Writing Workflow.

This workflow creates collaborative stories using multiple specialized agents:
1. Plot Designer - Creates the story premise and plot structure
2. Character Creator - Develops interesting characters
3. Scene Writer - Writes detailed scenes
4. Story Polisher - Adds final touches and improvements

You can provide different themes, genres, or settings to see how the story changes!
"""

from agent_framework import ChatAgent, WorkflowBuilder
from agent_framework.azure import AzureOpenAIChatClient

# Create Azure OpenAI chat client for all agents
chat_client = AzureOpenAIChatClient()

# Agent 1: Plot Designer
plot_designer = ChatAgent(
    name="PlotDesigner",
    description="An agent that creates story plots and structures",
    chat_client=chat_client,
    instructions="""You are a creative plot designer. When given a story idea or theme:
- Create an interesting plot premise in 2-3 sentences
- Identify the main conflict or challenge
- Suggest a story arc (beginning, middle, end)
- Set the mood and tone
- Be creative and engaging!
- Keep your response concise (under 150 words)
""",
)

# Agent 2: Character Creator
character_creator = ChatAgent(
    name="CharacterCreator",
    description="An agent that develops compelling characters",
    chat_client=chat_client,
    instructions="""You are a character development expert. Based on the plot provided:
- Create 2-3 main characters with distinct personalities
- Give each character a name and brief background
- Describe their motivations and goals
- Show how they relate to the plot
- Make them interesting and memorable!
- Keep your response concise (under 150 words)
""",
)

# Agent 3: Scene Writer
scene_writer = ChatAgent(
    name="SceneWriter",
    description="An agent that writes engaging story scenes",
    chat_client=chat_client,
    instructions="""You are a vivid scene writer. Using the plot and characters:
- Write an opening scene that hooks the reader
- Show (don't just tell) the characters in action
- Include dialogue if appropriate
- Use descriptive, engaging language
- Create atmosphere and tension
- Keep it to 200-250 words
""",
)

# Agent 4: Story Polisher
story_polisher = ChatAgent(
    name="StoryPolisher",
    description="An agent that adds final polish and improvements",
    chat_client=chat_client,
    instructions="""You are a story editor and polisher. Review the story created so far:
- Add a compelling title
- Write a brief conclusion or cliffhanger (2-3 sentences)
- Add any final touches to improve flow
- Ensure the story is cohesive and engaging
- Present the complete story with title, opening scene, and ending
- Format it nicely with proper paragraphs
""",
)

# Build the workflow - simple sequential flow
workflow = (
    WorkflowBuilder()
    .set_start_executor(plot_designer)
    .add_edge(plot_designer, character_creator)
    .add_edge(character_creator, scene_writer)
    .add_edge(scene_writer, story_polisher)
    .build()
)


def main():
    """Launch the story writing workflow in DevUI."""
    import logging

    from agent_framework.devui import serve

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    logger.info("Starting Interactive Story Writing Workflow")
    logger.info("Available at: http://localhost:8090")
    logger.info("Entity ID: workflow_story_writing")
    logger.info("\nTry prompts like:")
    logger.info("  - Write a sci-fi story about time travel")
    logger.info("  - Create a mystery story set in a haunted house")
    logger.info("  - Make a fantasy story about a dragon rider")
    logger.info("  - Write a comedy about a chef's cooking disaster")

    # Launch server with the workflow
    serve(entities=[workflow], port=8090, auto_open=True)


if __name__ == "__main__":
    main()
