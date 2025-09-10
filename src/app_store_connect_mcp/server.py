import asyncio
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from app_store_connect_mcp.core.container import Container


async def _run_server() -> None:
    load_dotenv()

    server = Server("app-store-connect-mcp")
    container = Container()

    # Get domain handlers with injected dependencies
    domain_handlers = container.get_domain_handlers()

    # Register tools
    @server.list_tools()
    async def handle_list_tools():
        tools = []
        for handler in domain_handlers:
            tools.extend(handler.get_tools())
        return tools

    # Build routing table
    tool_name_to_handler = {}
    for handler in domain_handlers:
        for tool in handler.get_tools():
            tool_name_to_handler[tool.name] = handler

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict):
        handler = tool_name_to_handler.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        return await handler.handle_tool(name, arguments)

    options = InitializationOptions(
        server_name="app-store-connect-mcp",
        server_version="0.1.0",
        capabilities={"tools": {"listChanged": False}},
    )

    async with stdio_server() as (read, write):
        try:
            await server.run(read, write, options)
        finally:
            await container.cleanup()


def run() -> None:
    asyncio.run(_run_server())


def main() -> None:
    run()
