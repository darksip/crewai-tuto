# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a CrewAI tutorial project - a Python application for exploring CrewAI framework capabilities. The project uses UV as the package manager and Python 3.11+ as the runtime.

## Development Commands

### Package Management
- `uv add <package>` - Add a new dependency
- `uv remove <package>` - Remove a dependency  
- `uv sync` - Install/update dependencies
- `uv run python main.py` - Run the main application

### Running the Application
- `uv run python main.py` - Execute the main script

## Architecture

- **main.py**: Entry point with a simple "Hello World" placeholder
- **pyproject.toml**: Project configuration with CrewAI dependencies
- **uv.lock**: Dependency lock file (UV package manager)

## Key Dependencies
- **crewai**: Core CrewAI framework (>=0.177.0)
- **pydantic**: Data validation (>=2.11.7) 
- **python-dotenv**: Environment variable management (>=1.1.1)

## Notes
- This appears to be a fresh project setup for CrewAI experimentation
- Uses UV instead of pip/poetry for dependency management
- Ready for CrewAI agent development and tutorials