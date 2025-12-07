from datetime import datetime

from loguru import logger
from strands import tool


@tool
def calculator(expression: str) -> str:
    """Evaluates a mathematical expression.

    Args:
        expression: Mathematical expression to evaluate
    """
    logger.info(f"Calculator tool called with: {expression}")
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e!s}"


@tool
def get_current_time() -> str:
    """Returns the current date and time."""
    logger.info("Current time tool called")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
