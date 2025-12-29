import os
import asyncio
import time
import logging
from google import genai
from google.genai import types

from client import MCPClient

# Configuration
RUN_MODE = os.getenv("RUN_MODE", "cli")
MCP_URL = os.getenv("MCP_URLS_CLI") if RUN_MODE == "cli" else os.getenv("MCP_URLS_PROD").split(",")[0] 
# Note: Production multiple clients logic omitted for MVP
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = "gemini-2.5-flash-lite" # User requested model
# MODEL_NAME = "gemini-1.5-flash" 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("saint-graph")

async def main():
    logger.info(f"Starting Saint Graph in {RUN_MODE} mode...")
    
    # 1. Connect to Body (MCP)
    # Note: In docker-compose, mcp-cli might take a moment to start.
    time.sleep(5) 
    client = MCPClient(base_url=MCP_URL)
    try:
        await client.connect()
    except Exception as e:
        logger.error(f"Failed to connect to MCP Body at {MCP_URL}: {e}")
        return

    # 2. Initialize Mind (Gemini)
    with open("mind/soul.md", "r", encoding="utf-8") as f:
        system_instruction = f.read()

    # We need to map MCP tools to Gemini Tools
    # For the MVP, we manually define the declarations to match server.py
    # Ideally, we convert client.tools to GenAI types.Tool
    
    # Tool Declarations
    gemini_tools = [
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
                # Note: get_comments is NOT given to Gemini as a tool to call.
                # The SYSTEM calls it, and feeds the result to Gemini.
            ]
        )
    ]

    genai_client = genai.Client(api_key=GOOGLE_API_KEY)
    chat = genai_client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=gemini_tools,
            temperature=1.0, # High temperature for lively character
        )
    )

    logger.info("Saint Graph Initialized. Entering Loop.")

    # 3. Main Loop
    while True:
        try:
            # Observation: Get Comments (Sensation)
            # We treat this as a system-level input
            comments = await client.call_tool("get_comments", {})
            
            # If no comments, we might still want to trigger the AI to say something occasionally
            # For MVP, we only trigger if there are comments OR randomly?
            # User rule: "If there are NO comments... chat about random topic"
            # So we ALWAYS trigger.
            
            user_message = f"[System/Observation]:\nUser Comments:\n{comments}"
            
            logger.info(f"Sending to Gemini: {user_message[:50]}...")
            
            # Send to Gemini
            response = chat.send_message(user_message)
            
            # Handle Tool Calls
            # The GenAI SDK might handle them for us if we used automatic_function_calling
            # But here we manually inspect parts.
            
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.text:
                         logger.warning(f"Gemini output text (ignoring/not speaking): {part.text}")
                    
                    if part.function_call:
                        fc = part.function_call
                        logger.info(f"Gemini decided to act: {fc.name}({fc.args})")
                        
                        # Execute logic on Body
                        await client.call_tool(fc.name, fc.args)
                        
                        # In a real chat loop, we should feed the tool result back.
                        # For "Action" tools like speak, the result is usually just confirmation.
                        # We can likely just ignore feeding it back for this simple loop 
                        # OR we need to maintain the turn structure.
                        # The GenAI SDK ChatSession expects function responses usually.
                        # Let's simple-hack: Send a "Tool executed" user message next turn?
                        # Or strictly, we should use the proper manual function calling flow.
                        
                        # Correct flow for ChatSession manual tool use:
                        # The session waits for function response.
                        # response = chat.send_message(types.Part(function_response=...))
                        # But since we are driving the loop, maybe we just send the NEW comments as the next user message
                        # and implies the previous tools succeeded.
                        # However, Gemini might get stuck waiting for function output.
                        
                        # Let's send the function response immediately
                        tool_output = "Executed."
                        chat.send_message(
                            types.Part(
                                function_response=types.FunctionResponse(
                                    name=fc.name,
                                    response={"result": tool_output}
                                )
                            )
                        )
            
            # Wait a bit before next cycle to respect Rate Limits (10 RPM = 1 per 6s, aiming for 10s+ safe)
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in Main Loop: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
