# Changelog

## [1.0.0] - 2026-05-13

### Added
- Initial release of Brainless MCP
- Single consolidated `unraid` tool with action+subaction routing
- `unraid_help` tool to discover all capabilities
- **System**: overview, CPU, memory, network, UPS metrics
- **Health**: ping, connection test, config dump
- **Docker**: full container lifecycle (list, start, stop, restart, pause, unpause, remove, logs, update all, autostart)
- **VMs**: full VM lifecycle (list, start, stop, pause, resume, reboot, force_stop, reset, remove, autostart)
- **Array**: status, start/stop, parity checks, shares CRUD, disk details, SMART tests
- **Notifications**: list, add, mark read, archive, delete
- **Users**: list, add, update, delete, set role
- **Plugins**: list, install, update, remove, check updates
- **Settings**: get/set, network config, reboot, shutdown, UPS config
- **Live**: 10 real-time WebSocket subscription types (cpu, memory, array, network, docker, vm, notifications, parity, disk_temps, logs)
- Async GraphQL client with token-bucket rate limiting (90 req/9s), 60s query cache, connection pooling
- Safety guards requiring `confirm=True` for 16 destructive operations
- Multi-transport support: stdio, HTTP, SSE
- Docker + docker-compose deployment support
- 44 unit tests covering all major components
