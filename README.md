# Textra Japanese to English Translator MCP Server

## Overview

This project provides a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that translates Japanese text into English using the [textra](https://mt-auto-minhon-mlt.ucri.jgn-x.jp/) translation API service.

It is particularly useful for interacting with LLMs that have limited Japanese language understanding. By routing Japanese instructions through this MCP server, the input can be translated into English before being passed to the LLM.

This server is built using the `fastmcp` framework.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```
    *(On Windows, use `.venv\Scripts\activate`)*
3.  **Install dependencies:**
    Install the necessary libraries for running the project and for development/testing.
    ```bash
    # Install runtime dependencies only
    uv pip install .

    # Install runtime and development/testing dependencies
    uv pip install '.[dev]'
    ```
    (Dependencies are installed based on `pyproject.toml`.)
4.  **Set Environment Variables:**
    This server **requires** the following environment variables to be set with your Textra API credentials:
    *   `TEXTRA_API_KEY`: Your Textra API Key.
    *   `TEXTRA_API_SECRET`: Your Textra API Secret.
    *   `TEXTRA_USER_NAME`: Your Textra Login ID.

    It is **strongly recommended** to set these variables in your shell's configuration file (e.g., `~/.bashrc`, `~/.zshrc`, `~/.config/fish/config.fish`) rather than using a `.env` file. This ensures the variables are available when the MCP server is run by client applications.

    Example for `.zshrc` or `.bashrc`:
    ```bash
    export TEXTRA_API_KEY="your_api_key"
    export TEXTRA_API_SECRET="your_api_secret"
    export TEXTRA_USER_NAME="your_username"
    ```
    Remember to source the file (e.g., `source ~/.zshrc`) or restart your shell after adding these lines.

    *Optional Variables:*
    *   `TEXTRA_JA_EN_API_URL`: Overrides the default translation API endpoint.
    *   `TEXTRA_TOKEN_URL`: Overrides the default OAuth token endpoint.

    *(See `.env.example` for variable names and default values. While using a `.env` file is possible for local development, especially with `fastmcp dev`, setting system-wide environment variables is more robust for MCP server deployment.)*

## Running Tests

Ensure your virtual environment is activated.

```bash
pytest
```
or
```bash
uv run test
```

## Usage

Ensure your virtual environment is activated and the **required environment variables** (`TEXTRA_API_KEY`, `TEXTRA_API_SECRET`, `TEXTRA_USER_NAME`) are correctly set in your shell environment.

### Running the Server Locally

There are two main ways to run the server locally:

1.  **Using `fastmcp dev` (Recommended for development):**
    This command provides features like auto-reloading on code changes.
    ```bash
    fastmcp dev server.py
    ```

2.  **Using `uvx`:**
    This command runs the server script directly within a temporary environment managed by `uv`, installing dependencies as needed. It's useful for quick execution without installation.
    ```bash
    uvx python server.py
    ```

Both commands will start the server, listening for MCP connections via stdio by default. You can then connect to it using an MCP client like the MCP Inspector.

3.  **Using `uvx` directly from GitHub (Requires `uv` installed):**
    You can run the server directly from the GitHub repository without cloning it first. This is useful for integrating with MCP clients that support custom commands. `uvx` will handle fetching the code and installing dependencies in a temporary environment.
    ```bash
    uvx python server.py --git https://github.com/hokupod/textra-ja-to-en-mcp.git
    ```
    *Note: This method might take longer to start initially compared to running from a local clone.*

### Installing the Server for MCP Clients (e.g., Claude Desktop)

Use the `fastmcp install` command to make the server available to MCP client applications on your system.

```bash
fastmcp install server.py --name "Japanese to English Translator"
```

After installation, MCP clients like Claude Desktop should be able to discover and use the "Japanese to English Translator" tool.

Alternatively, if your MCP client supports defining servers via commands (like Claude Desktop's `mcp_servers.json`), you can configure it to run the server directly from GitHub using `uvx`:

```json
{
  "mcpServers": {
    "textra-translator": {
      "command": "uvx",
      "args": [
        "python",
        "server.py",
        "--git", "https://github.com/hokupod/textra-ja-to-en-mcp.git"
        // Optionally specify a branch or commit:
        // "--git", "https://github.com/hokupod/textra-ja-to-en-mcp.git#main"
      ]
    }
  }
}
```
*(Ensure `uv` is installed and accessible in the client's environment.)*

When interacting with an LLM through such a client, if you provide input in Japanese, the LLM (if configured to use this tool appropriately based on its description) should automatically invoke this server to translate the text to English before processing the request further. The translated English text will then be treated as the user's original request.
