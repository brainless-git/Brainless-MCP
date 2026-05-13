# Brainless MCP

Full-control MCP server for Unraid — lets Claude (or any MCP client) manage your Unraid server via its GraphQL API.

## Features

| Domain | Operations |
|--------|------------|
| **System** | Overview, CPU, memory, network, UPS |
| **Health** | Ping, connection test, config dump |
| **Docker** | List, start, stop, restart, pause, logs, update all, remove |
| **VMs** | List, start, stop, pause, resume, reboot, force-stop, reset, remove |
| **Array** | Status, start/stop, parity checks, shares CRUD |
| **Disks** | Details, SMART test/report, remove, clear stats |
| **Notifications** | List, add, mark read, archive, delete |
| **Users** | List, add, update, delete, set role |
| **Plugins** | List, install, update, remove, check updates |
| **Settings** | Get/set settings, network config, reboot, shutdown |
| **Live** | Real-time WebSocket subscriptions (CPU, memory, array, docker events, …) |

## Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Unraid API key (generate in Unraid UI: **Settings → Management Access → API Keys**)

### Install & run

```bash
# Clone
git clone https://github.com/brainless-git/brainless-mcp
cd brainless-mcp

# Copy and fill in your credentials
cp .env.example .env
$EDITOR .env

# Run (stdio transport for Claude Desktop / Claude Code)
uv run brainless-mcp-server
```

### Docker

```bash
cp .env.example .env
$EDITOR .env
docker compose up -d
```

## Configuration

All options are set via environment variables (or a `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `UNRAID_API_URL` | `https://tower.local` | Unraid server URL |
| `UNRAID_API_KEY` | *(required)* | Unraid API key |
| `UNRAID_VERIFY_SSL` | `false` | `true`, `false`, or path to CA bundle |
| `BRAINLESS_MCP_BEARER_TOKEN` | *(empty)* | Token MCP clients must present (leave empty to disable auth) |
| `BRAINLESS_MCP_TRANSPORT` | `stdio` | `stdio` \| `http` \| `sse` |
| `BRAINLESS_MCP_PORT` | `8000` | HTTP port (non-stdio transports) |
| `BRAINLESS_MCP_LOG_LEVEL` | `INFO` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` |
| `BRAINLESS_MCP_LOG_FILE` | *(empty)* | Log file path (logs to stderr if empty) |
| `UNRAID_AUTO_START_SUBSCRIPTIONS` | `false` | Auto-start all live WebSocket subscriptions on startup |
| `UNRAID_MAX_RECONNECT_ATTEMPTS` | `10` | Max WebSocket reconnect attempts before giving up |

## Claude Desktop / Claude Code setup

Add to your MCP config (e.g. `~/.claude/mcp.json`):

```json
{
  "mcpServers": {
    "brainless-mcp": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/brainless-mcp", "brainless-mcp-server"],
      "env": {
        "UNRAID_API_URL": "https://192.168.1.100",
        "UNRAID_API_KEY": "your_api_key",
        "UNRAID_VERIFY_SSL": "false"
      }
    }
  }
}
```

## Usage

The server exposes two MCP tools:

### `unraid`
Single consolidated tool. Provide `action` + `subaction` + optional `params`.

```
action='docker'  subaction='list'
action='docker'  subaction='start'   params={'id': 'my-container'}
action='vm'      subaction='start'   params={'name': 'Windows10'}
action='array'   subaction='status'
action='array'   subaction='stop'    confirm=True
action='docker'  subaction='remove'  params={'id': 'abc'} confirm=True
action='live'    subaction='start'   params={'name': 'cpu'}
action='live'    subaction='read'    params={'name': 'cpu', 'limit': 10}
action='health'  subaction='ping'
```

### `unraid_help`
Lists all available actions and subactions.

```
unraid_help()                     # show all
unraid_help(action='docker')      # show docker subactions only
```

## Safety

Destructive operations (stopping the array, removing containers/VMs, deleting users, etc.) require `confirm=True` and will raise an error otherwise. This prevents accidental data loss from a misread instruction.

## Live Subscriptions

Real-time data via WebSocket:

| Name | Data |
|------|------|
| `cpu` | Per-core load |
| `memory` | Usage stats |
| `array` | Array state & disk status |
| `network` | Interface rx/tx |
| `docker` | Container lifecycle events |
| `vm` | VM state changes |
| `notifications` | New notifications |
| `parity` | Parity check progress |
| `disk_temps` | Disk temperatures |
| `logs` | Syslog lines |

```
# Start collecting CPU data
action='live' subaction='start' params={'name': 'cpu'}

# Read the last 20 data points
action='live' subaction='read'  params={'name': 'cpu', 'limit': 20}

# Stop
action='live' subaction='stop'  params={'name': 'cpu'}
```

## Development

```bash
# Install with dev deps
uv sync --extra dev

# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/
```
