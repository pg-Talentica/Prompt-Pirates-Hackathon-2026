# Task-001: Project Setup & Structure

## Summary
Establish the repository structure, dependency management, configuration pattern, and a runnable skeleton so all later work has a consistent base.

## Scope
- Create folder structure: `agents/`, `tools/`, `memory/`, `api/`, `ui/`
- Python backend: FastAPI, LangGraph, and core dependencies (requirements.txt or pyproject.toml)
- React frontend: base app with WebSocket client placeholder
- Configuration: env vars only (e.g. `.env.example` with `LLM_API_KEY`, `MODEL`, etc.); no hardcoded secrets
- Docker: `docker-compose.yml` that builds and runs backend + frontend (or serves UI via backend)
- README: placeholder with project title, how to run (e.g. `docker-compose up`), and link to env setup

## Acceptance Criteria
- [ ] All directories exist and are documented in README
- [ ] Backend starts without errors; frontend (or static serve) is reachable
- [ ] All config read from environment; `.env.example` committed, `.env` in `.gitignore`
- [ ] `docker-compose up` brings up the stack and README reflects this

## Dependencies
- None (first task)

## Notes
- Keep agents/, tools/, memory/ empty stubs until later tasks; focus on structure and runnability.
