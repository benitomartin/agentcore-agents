from agentcore_agents.browser.setup import get_browser_tool
from agentcore_agents.tools.local import calculator, get_current_time

browser_tool_instance = get_browser_tool()
TOOLS = [calculator, get_current_time, browser_tool_instance.browser]
