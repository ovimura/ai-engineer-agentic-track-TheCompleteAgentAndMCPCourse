import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from agents.mcp import MCPServerStdio, create_static_tool_filter

load_dotenv(override=True)

PROJECT_DIR = str(Path(__file__).resolve().parent.parent)
tavily_env = {"TAVILY_API_KEY": os.getenv("TAVILY_API_KEY")}
TIMEOUT = 120


def _python_server(module: str) -> dict:
    """Launch a local FastMCP module as the MCP child process.

    `uv run` starts a wrapper, then Python. MCP stdio needs the server itself
    to own stdin/stdout; that extra process closes the pipe on Windows.
    """
    return {"command": sys.executable, "args": ["-m", module], "cwd": PROJECT_DIR}


def _tool_server(command: str, args: list[str], env: dict | None = None) -> dict:
    """Launch a third-party stdio MCP server (uvx / npx)."""
    params: dict = {"command": command, "args": args, "cwd": PROJECT_DIR}
    if env:
        params["env"] = env
    return params


# The market data server for the trader.
# Massive's MCP package currently pulls mcp 2.x, which removed FastMCP and
# crashes stdio. Our market_server already calls get_share_price(), which uses
# live Massive data when MASSIVE_API_KEY is set, so it is the reliable child.
market_params = _python_server("backend.market_server")


def trader_mcp_servers() -> list[MCPServerStdio]:
    """The trader's MCP servers: our Accounts server, Push Notification and Market data."""
    params = [
        _python_server("backend.accounts_server"),
        _python_server("backend.push_server"),
        market_params,
    ]
    return [MCPServerStdio(p, client_session_timeout_seconds=TIMEOUT) for p in params]


def researcher_mcp_servers(name: str) -> list[MCPServerStdio]:
    """The researcher's MCP servers: Fetch, Tavily web search and Memory.

    Tavily's server offers several tools; we restrict it to web search so the
    researcher reaches for plain search rather than its heavier crawl or deep-research tools.
    """
    fetch = MCPServerStdio(
        _tool_server("uvx", ["--with", "mcp<2", "mcp-server-fetch"]),
        client_session_timeout_seconds=TIMEOUT,
    )
    search = MCPServerStdio(
        _tool_server("npx", ["-y", "tavily-mcp@latest"], env=tavily_env),
        client_session_timeout_seconds=TIMEOUT,
        tool_filter=create_static_tool_filter(allowed_tool_names=["tavily_search"]),
    )
    memory = MCPServerStdio(
        _tool_server("npx", ["-y", "mcp-memory-libsql"], env={"LIBSQL_URL": f"file:./memory/{name}.db"}),
        client_session_timeout_seconds=TIMEOUT,
    )
    return [fetch, search, memory]
