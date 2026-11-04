# Bitburner AI OS

A local, single player system for an AI to learn the official Bitburner game through visible Chromium interactions and legitimate in-game Netscript. It uses the maintained Browser Use Python library, Ollama compatible local inference, and Docker Compose.

This repository is public. Do not commit `.env`, LAN addresses, private hostnames, credentials, SSH keys, exported game saves, browser profiles, screenshots, or local instance records. The deployment uses placeholders for site-specific values.

## Status

This is an active homelab deployment. See the [architecture](docs/architecture.md), [operator guide](docs/operator-guide.md), and [validation record](docs/validation.md). Those documents distinguish verified behavior from outstanding acceptance work.

## Layout

- `app/`: minimal control API and browser agent.
- `deployment/`: container image, Compose, environment template, and cloud-init template.
- `docs/`: architecture, operation, and validation evidence.
- Runtime profile, game saves, checkpoints, action logs, screenshots, and backups stay outside source control under `/opt/bitburner-agent/`.

The service binds to localhost. Reach it with an SSH tunnel from an authorized workstation. The agent has no host shell, Docker socket, arbitrary file tools, or direct game-state interface.
