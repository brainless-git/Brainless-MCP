# Brainless MCP

Full-control MCP server for Unraid — lets Claude (or any MCP client) manage your Unraid server via its GraphQL API.

[![CI](https://github.com/brainless-git/Brainless-MCP/actions/workflows/ci.yml/badge.svg)](https://github.com/brainless-git/Brainless-MCP/actions/workflows/ci.yml)
[![Docker](https://github.com/brainless-git/Brainless-MCP/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/brainless-git/Brainless-MCP/actions/workflows/docker-publish.yml)
[![Docker Image](https://img.shields.io/docker/v/brainless86/brainless-mcp/latest?label=Docker%20Hub)](https://hub.docker.com/r/brainless86/brainless-mcp)

## Features

| Domain | Operations |
|--------|------------|
| **System** | Overview, CPU, memory, network, UPS |
| **Health** | Ping, connection test, config dump |
| **Docker** | List, images, networks, start, stop, restart, pause, unpause, logs, update all, remove, autostart |
| **VMs** | List, start, stop, pause, resume, reboot, force-stop, reset, remove, autostart |
| **Array** | Status, start/stop, parity checks (start/pause/resume/cancel), shares CRUD |
| **Disks** | Details, SMART test/report, remove, clear stats |
| **Notifications** | List, archived, add, mark read, archive, delete |
| **Users** | List, add, update, delete, set role |
| **Plugins** | List, install, update, remove, check updates |
| **Settings** | Get/set, network config, reboot, shutdown, UPS config |
| **Live** | 10 real-time WebSocket subscriptions (CPU, memory, array, network, Docker events, VM events, parity, disk temps, syslog) |

## Quick Start

### Option 1 — Docker Hub (recommended)

The easiest way to run Brainless MCP. The image is published to Docker Hub on every merge to `main`.

```bash
docker run -d \
  --name brainless-mcp \
  --restart unless-stopped \
  -p 8000:8000 \
  -e UNRAID_API_URL=https://192.168.1.100 \
  -e UNRAID_API_KEY=your_api_key \
  -e UNRAID_VERIFY_SSL=false \
  -e BRAINLESS_MCP_TRANSPORT=http \
  brainless86/brainless-mcp:latest
```

Or with Docker Compose:

```bash
cp .env.example .env
$EDITOR .env          # fill in UNRAID_API_URL and UNRAID_API_KEY
docker compose up -d
```

### Option 2 — Run from source

```bash
# Prerequisites: Python 3.12+, uv (https://docs.astral.sh/uv/)
git clone https://github.com/brainless-git/Brainless-MCP
cd Brainless-MCP

cp .env.example .env
$EDITOR .env

# stdio transport (for Claude Desktop / Claude Code)
uv run brainless-mcp-server
```

## Configuration

All options are set via environment variables or a `.env` file (copy `.env.example` to get started):

| Variable | Default | Description |
|----------|---------|-------------|
| `UNRAID_API_URL` | `https://tower.local` | Unraid server URL |
| `UNRAID_API_KEY` | *(required)* | Unraid API key — generate in **Settings → Management Access → API Keys** |
| `UNRAID_VERIFY_SSL` | `false` | `true`, `false`, or path to a CA bundle |
| `BRAINLESS_MCP_BEARER_TOKEN` | *(empty)* | Token MCP clients must present — leave empty to disable auth |
| `BRAINLESS_MCP_TRANSPORT` | `stdio` | `stdio` \| `http` \| `sse` |
| `BRAINLESS_MCP_PORT` | `8000` | HTTP listen port (non-stdio transports only) |
| `BRAINLESS_MCP_LOG_LEVEL` | `INFO` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` |
| `BRAINLESS_MCP_LOG_FILE` | *(empty)* | Log file path — logs to stderr if empty |
| `UNRAID_AUTO_START_SUBSCRIPTIONS` | `false` | Auto-start all 10 live WebSocket subscriptions on startup |
| `UNRAID_MAX_RECONNECT_ATTEMPTS` | `10` | Max WebSocket reconnect attempts before giving up |

## Claude Desktop / Claude Code setup

### Using the Docker image (HTTP transport)

```json
{
  "mcpServers": {
    "brainless-mcp": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Using uv from source (stdio transport)

```json
{
  "mcpServers": {
    "brainless-mcp": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/Brainless-MCP", "brainless-mcp-server"],
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
action='health'  subaction='ping'
action='system'  subaction='overview'

action='docker'  subaction='list'
action='docker'  subaction='start'    params={'id': 'my-container'}
action='docker'  subaction='logs'     params={'id': 'my-container', 'tail': 50}
action='docker'  subaction='remove'   params={'id': 'abc'} confirm=True

action='vm'      subaction='list'
action='vm'      subaction='start'    params={'name': 'Windows10'}
action='vm'      subaction='force_stop' params={'name': 'Windows10'} confirm=True

action='array'   subaction='status'
action='array'   subaction='stop'     confirm=True
action='array'   subaction='parity_check' params={'correct': True}
action='array'   subaction='smart_test'   params={'id': 'sda', 'type': 'short'}

action='live'    subaction='start'    params={'name': 'cpu'}
action='live'    subaction='read'     params={'name': 'cpu', 'limit': 20}
action='live'    subaction='stop'     params={'name': 'cpu'}
action='live'    subaction='start_all'
```

### `unraid_help`

Lists all available actions and subactions.

```
unraid_help()                      # show everything
unraid_help(action='docker')       # show docker subactions only
```

## Safety

Destructive operations require `confirm=True` and raise an error without it. This prevents accidental data loss from a misread instruction.

Protected operations include: stopping the array, removing disks, removing containers/VMs, deleting users, removing plugins, and more. Full list in `src/brainless_mcp/core/guards.py`.

## Live Subscriptions

Real-time data streams via persistent WebSocket connections to Unraid:

| Name | Data |
|------|------|
| `cpu` | Per-core load |
| `memory` | Total / free / used / swap |
| `array` | Array state & per-disk status |
| `network` | Interface rx/tx bytes per second |
| `docker` | Container lifecycle events |
| `vm` | VM state changes |
| `notifications` | Newly added notifications |
| `parity` | Parity check action, percent, speed, errors |
| `disk_temps` | Per-disk temperature & SMART status |
| `logs` | Syslog lines (timestamp, level, message) |

Data is buffered in memory (up to 100 events per subscription). WebSocket connections automatically reconnect with exponential backoff on failure.

## Architecture

```
src/brainless_mcp/
├── config/         settings (env vars, .env files)
├── core/
│   ├── client.py   async GraphQL client — rate limiting, query cache, connection pooling
│   ├── guards.py   destructive-action safety checks
│   └── exceptions.py
├── tools/
│   ├── unraid.py   consolidated tool router
│   ├── _docker.py  _vm.py  _array.py  _system.py  _health.py
│   ├── _user.py    _plugin.py  _notification.py  _setting.py  _live.py
├── server.py       FastMCP server + middleware
└── main.py         entry point + transport selection
```

**GraphQL client** — token-bucket rate limiter (90 tokens, 9 tokens/s), 60-second query cache, separate 90-second timeout for disk operations.

## CI / CD

| Workflow | Trigger | Action |
|----------|---------|--------|
| `ci.yml` | Push / PR to `main` | Runs `pytest` (44 tests) |
| `docker-publish.yml` | Merge to `main` or `v*.*.*` tag | Builds multi-arch image (`amd64` + `arm64`), pushes to `brainless86/brainless-mcp` |

## Development

```bash
uv sync --extra dev       # install with dev dependencies
uv run pytest             # run tests
uv run ruff check src/ tests/   # lint
```
