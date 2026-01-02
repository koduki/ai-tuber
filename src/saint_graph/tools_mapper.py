from typing import Dict, Any
from google.genai import types

def convert_schema(schema: Dict[str, Any]) -> types.Schema:
    """
    Recursively converts a JSON Schema dictionary to a Google GenAI types.Schema.
    Simplified implementation for common cases.
    """
    if not schema:
        return None

    type_str = schema.get("type", "OBJECT").upper()
    description = schema.get("description")

    # Handle properties for Objects
    properties = {}
    if "properties" in schema:
        for key, prop_schema in schema["properties"].items():
            properties[key] = convert_schema(prop_schema)

    # Handle items for Arrays
    items = None
    if "items" in schema:
        items = convert_schema(schema["items"])

    # Handle enum
    enum_values = schema.get("enum")

    # Handle required fields (passed at parent level in JSON Schema, but GenAI Schema handles it structurally or via required list in FunctionDeclaration parameters?
    # Actually types.Schema has 'required' list if it is an object.
    required = schema.get("required", [])

    return types.Schema(
        type=getattr(types.Type, type_str, types.Type.OBJECT),
        description=description,
        properties=properties if properties else None,
        items=items,
        enum=enum_values,
        required=required if required else None
    )

def convert_mcp_tool_to_genai(mcp_tool: Dict[str, Any]) -> types.FunctionDeclaration:
    """
    Converts a single MCP tool definition to a Gemini FunctionDeclaration.
    """
    return types.FunctionDeclaration(
        name=mcp_tool["name"],
        description=mcp_tool.get("description", ""),
        parameters=convert_schema(mcp_tool.get("inputSchema", {}))
    )
