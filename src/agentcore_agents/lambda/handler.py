import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def calculator(expression: str) -> str:
    logger.info(f"Calculator tool called with: {expression}")
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e!s}"


def get_current_time() -> str:
    logger.info("Current time tool called")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    delimiter = "___"
    
    tool_name_full = ""
    if (
        hasattr(context, "client_context")
        and context.client_context
        and hasattr(context.client_context, "custom")
    ):
        tool_name_full = context.client_context.custom.get("bedrockAgentCoreToolName", "")
    
    if not tool_name_full and hasattr(context, "bedrockAgentCoreToolName"):
        tool_name_full = context.bedrockAgentCoreToolName
    
    if delimiter in tool_name_full:
        tool_name = tool_name_full[tool_name_full.index(delimiter) + len(delimiter) :]
    else:
        tool_name = tool_name_full
    
    logger.info(f"Lambda invoked with tool: {tool_name}, full name: {tool_name_full}")
    logger.info(f"Event: {event}")
    
    try:
        if tool_name == "calculator":
            expression = event.get("expression", "")
            if not expression:
                return {"error": "Missing required parameter: expression"}
            result = calculator(expression)
            return {"result": result}
        
        elif tool_name == "get_current_time":
            result = get_current_time()
            return {"result": result}
        
        else:
            logger.error(f"Unknown tool: {tool_name}")
            return {"error": f"Unknown tool: {tool_name}"}
    
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return {"error": str(e)}

