from typing import List
from google.genai import types

def get_tool_definitions() -> List[types.Tool]:
    """
    モデルに提供するツール定義を返します。
    """
    return [
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
