import os
import asyncio
import logging
from typing import List

# Google ADK & GenAI
from google.genai import types
from google.adk.models import Gemini
from google.adk.models.llm_request import LlmRequest

# Custom MCP Client
from mcp_client import MCPClient

# Configuration
RUN_MODE = os.getenv("RUN_MODE", "cli")
MCP_URL = os.getenv("MCP_URLS_CLI") if RUN_MODE == "cli" else os.getenv("MCP_URLS_PROD").split(",")[0]
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = "gemini-2.0-flash-lite" # Use the requested lite model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("saint-graph")

async def main():
    logger.info(f"Starting Saint Graph in {RUN_MODE} mode (ADK-based)...")

    # 1. Connect to Body (MCP) via mcp_client.py
    await asyncio.sleep(2) # Give body some time to start if needed
    client = MCPClient(base_url=MCP_URL)
    try:
        await client.connect()
    except Exception as e:
        logger.error(f"Failed to connect to MCP Body at {MCP_URL}: {e}")
        return

    # 2. Initialize Mind (Persona)
    persona_path = os.path.join(os.path.dirname(__file__), "..", "mind", "ren", "persona.md")
    persona_path = os.path.normpath(persona_path)
    
    # Simple search for persona.md
    if not os.path.exists(persona_path):
        paths_to_try = ["/workspaces/ai-tuber/src/mind/ren/persona.md", "src/mind/ren/persona.md", "mind/ren/persona.md"]
        for p in paths_to_try:
            if os.path.exists(p):
                persona_path = p
                break

    try:
        with open(persona_path, "r", encoding="utf-8") as f:
            system_instruction = f.read()
    except Exception as e:
        logger.error(f"Could not read persona file at {persona_path}: {e}")
        system_instruction = "You are a helpful AI Tuber."

    # 3. Define Tools
    tool_definitions = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="speak",
                    description="Speak text to the audience.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "text": types.Schema(type="STRING"),
                            "style": types.Schema(type="STRING", description="style: normal, happy, sad, etc.")
                        },
                        required=["text"]
                    )
                ),
                types.FunctionDeclaration(
                    name="change_emotion",
                    description="Change facial expression.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "emotion": types.Schema(type="STRING", description="emotion: neutral, happy, sad, angry, surprised")
                        },
                        required=["emotion"]
                    )
                ),
                types.FunctionDeclaration(
                    name="switch_scene",
                    description="Switch OBS scene.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "scene": types.Schema(type="STRING")
                        },
                        required=["scene"]
                    )
                ),
            ]
        )
    ]

    # 4. Initialize ADK Model
    model = Gemini(model=MODEL_NAME)
    logger.info(f"Saint Graph Initialized using {MODEL_NAME}. Entering Loop.")

    # 5. Main Loop
    chat_history: List[types.Content] = []

    while True:
        try:
            # Observation: Fetch new comments from Body
            comments = await client.call_tool("get_comments", {})
            user_message = f"[System/Observation]:\nUser Comments:\n{comments}"
            
            logger.info(f"Turn started. Input: {comments[:30]}...")
            
            # Add user message to history
            chat_history.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

            # Prepare request
            llm_request = LlmRequest(
                model=MODEL_NAME,
                contents=chat_history,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=tool_definitions,
                    temperature=1.0,
                )
            )

            # Process response
            model_response_parts = []
            async for response_chunk in model.generate_content_async(llm_request, stream=False):
                if response_chunk.content and response_chunk.content.parts:
                    for part in response_chunk.content.parts:
                        model_response_parts.append(part)
                        
                        if part.text:
                            logger.info(f"Gemini: {part.text}")
                        
                        if part.function_call:
                            fc = part.function_call
                            logger.info(f"ACTION: {fc.name}({fc.args})")
                            
                            # Execute tool
                            try:
                                result = await client.call_tool(fc.name, fc.args)
                                
                                # Record interaction in history
                                chat_history.append(types.Content(role="model", parts=[part]))
                                chat_history.append(
                                    types.Content(
                                        role="user",
                                        parts=[
                                            types.Part(
                                                function_response=types.FunctionResponse(
                                                    name=fc.name,
                                                    response={"result": str(result)}
                                                )
                                            )
                                        ]
                                    )
                                )
                            except Exception as e:
                                logger.error(f"Tool execution failed: {e}")

            # If Gemini just sent text without tool calls, add that to history too
            if model_response_parts and not any(p.function_call for p in model_response_parts):
                 chat_history.append(types.Content(role="model", parts=model_response_parts))

            # Prune history to keep context windows reasonable
            if len(chat_history) > 12:
                chat_history = chat_history[-12:]

            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in Main Loop: {e}", exc_info=True)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
