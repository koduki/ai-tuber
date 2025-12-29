import os
import asyncio
import logging
from typing import List

# Google ADK & GenAI
from google.genai import types
from google.adk.models import Gemini
from google.adk.models.llm_request import LlmRequest


# Custom MCP Client (until we migrate to ADK MCP if available)
from client import MCPClient

# Configuration
RUN_MODE = os.getenv("RUN_MODE", "cli")
MCP_URL = os.getenv("MCP_URLS_CLI") if RUN_MODE == "cli" else os.getenv("MCP_URLS_PROD").split(",")[0]
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = "gemini-2.5-flash" # Corrected model name for better compatibility

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("saint-graph")

async def main():
    logger.info(f"Starting Saint Graph in {RUN_MODE} mode (ADK-based)...")

    # 1. Connect to Body (MCP)
    await asyncio.sleep(5)
    client = MCPClient(base_url=MCP_URL)
    try:
        await client.connect()
    except Exception as e:
        logger.error(f"Failed to connect to MCP Body at {MCP_URL}: {e}")
        return

    # 2. Initialize Mind (Persona)
    persona_path = os.path.join(os.path.dirname(__file__), "..", "mind", "ren", "persona.md")
    persona_path = os.path.normpath(persona_path)
    # Fallback to mounted path if relative path doesn't work
    if not os.path.exists(persona_path):
        persona_path = "/app/mind/persona.md"
    if not os.path.exists(persona_path):
        persona_path = "mind/persona.md"
    
    with open(persona_path, "r", encoding="utf-8") as f:
        system_instruction = f.read()

    # 3. Define Tools (ADK Style - using GenAI types)
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
                            "style": types.Schema(type="STRING", description="style of speech: normal, happy, sad, etc.")
                        },
                        required=["text"]
                    )
                ),
                types.FunctionDeclaration(
                    name="change_emotion",
                    description="Change the avatar's facial expression.",
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
                    description="Switch the OBS scene.",
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

    logger.info("Saint Graph Initialized. Entering Loop.")

    # 5. Main Loop
    # We will manage the chat history manually in a list of contents.
    chat_history: List[types.Content] = []

    while True:
        try:
            # Observation
            comments = await client.call_tool("get_comments", {})
            user_message = f"[System/Observation]:\nUser Comments:\n{comments}"
            
            logger.info(f"Sending to Gemini: {user_message[:50]}...")
            
            # Add user message to history
            chat_history.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

            # Prepare request for the model
            llm_request = LlmRequest(
                model=MODEL_NAME,
                contents=chat_history,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=tool_definitions,
                    temperature=1.0,
                )
            )

            # Get response from the model
            # Collect all response chunks first, then process the final one
            all_chunks = []
            async for response_chunk in model.generate_content_async(llm_request, stream=True):
                all_chunks.append(response_chunk)
            
            # Process the last chunk (which should contain the complete response)
            if all_chunks:
                final_chunk = all_chunks[-1]
                logger.debug(f"Processing final chunk: {type(final_chunk)}")
                
                model_response_parts = []
                function_call_handled = False
                
                # ADK returns LlmResponse with candidates.content.parts structure
                if hasattr(final_chunk, 'candidates') and final_chunk.candidates:
                    for candidate in final_chunk.candidates:
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts'):
                                for part in candidate.content.parts:
                                    model_response_parts.append(part)
                                    
                                    # Check for text
                                    if hasattr(part, 'text') and part.text:
                                        logger.warning(f"Gemini text: {part.text}")
                                    
                                    # Check for function_call
                                    if hasattr(part, 'function_call') and part.function_call:
                                        fc = part.function_call
                                        logger.info(f"Action: {fc.name}({fc.args})")
                                        function_call_handled = True
                                        
                                        # Execute logic on Body
                                        await client.call_tool(fc.name, fc.args)
                                        
                                        # We will send the result back in the next turn's history
                                        chat_history.append(types.Content(role="model", parts=[part]))
                                        chat_history.append(
                                            types.Content(
                                                role="user",
                                                parts=[
                                                    types.Part(
                                                        function_response=types.FunctionResponse(
                                                            name=fc.name,
                                                            response={"result": "Executed."}
                                                        )
                                                    )
                                                ]
                                            )
                                        )
            
            # Add model's final response to history if it wasn't a function call
            if any(p.function_call for p in model_response_parts):
                pass # Already handled
            else:
                 chat_history.append(types.Content(role="model", parts=model_response_parts))


            # Prune history to avoid excessive length (optional, basic implementation)
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]

            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in Main Loop: {e}", exc_info=True)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
