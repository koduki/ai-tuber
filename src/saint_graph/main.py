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

# Silence noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("mcp_client").setLevel(logging.WARNING)
logging.getLogger("google_adk").setLevel(logging.WARNING)

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
    poll_count = 0
    POLL_INTERVAL = 0.5
    SOLILOQUY_INTERVAL = 30.0 # 30 seconds of silence triggers a random talk

    while True:
        try:
            # Observation: Fetch new comments from Body (Fast Polling)
            comments = await client.call_tool("get_comments", {})
            
            # Decide whether to invoke the Soul (Saint Graph)
            has_comments = comments != "No new comments."
            is_time_for_soliloquy = (poll_count * POLL_INTERVAL) >= SOLILOQUY_INTERVAL
            
            if not has_comments and not is_time_for_soliloquy:
                poll_count += 1
                await asyncio.sleep(POLL_INTERVAL)
                continue

            # Reset poll counter
            poll_count = 0
            
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

            # Process response (Soul cycle)
            while True:
                llm_request = LlmRequest(
                    model=MODEL_NAME,
                    contents=chat_history,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        tools=tool_definitions,
                        temperature=1.0,
                    )
                )

                final_response = None
                printed_len = 0
                async for chunk in model.generate_content_async(llm_request, stream=True):
                    if chunk.content and chunk.content.parts:
                        # Stream text deltas to logger for speed feel
                        full_text = "".join(p.text for p in chunk.content.parts if p.text)
                        if len(full_text) > printed_len:
                            logger.info(f"Gemini: {full_text[printed_len:]}")
                            printed_len = len(full_text)
                    
                    if not chunk.partial:
                        final_response = chunk

                if not final_response or not final_response.content:
                    break

                # Record Soul's response once to history
                chat_history.append(final_response.content)
                
                # Check for tool calls
                fcs = [p.function_call for p in final_response.content.parts if p.function_call]
                if not fcs:
                    break # Soul is satisfied for this observation
                
                # Execute tools
                tool_results = []
                for fc in fcs:
                    logger.info(f"ACTION: {fc.name}({fc.args})")
                    try:
                        res = await client.call_tool(fc.name, fc.args)
                        tool_results.append(
                            types.Part(
                                function_response=types.FunctionResponse(
                                    name=fc.name,
                                    response={"result": str(res)}
                                )
                            )
                        )
                    except Exception as e:
                        logger.error(f"Tool execution failed: {e}")
                
                # Feed tool results back and continue Soul cycle immediately
                chat_history.append(types.Content(role="user", parts=tool_results))

            # Prune history to keep context windows reasonable
            if len(chat_history) > 12:
                chat_history = chat_history[-12:]

            # Small delay after LLM turn to prevent overwhelming
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in Main Loop: {e}", exc_info=True)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
