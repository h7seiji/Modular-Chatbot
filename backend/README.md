# Modular Chatbot Backend

A modern Python backend for the modular chatbot system featuring RouterAgent and specialized AI agents.

## Features

- **RouterAgent**: Intelligent query routing to specialized agents
- **KnowledgeAgent**: RAG-based responses using InfinitePay help content with web scraping and vector embeddings (Gemini/OpenAI)
- **MathAgent**: Mathematical expression solving with LLM interpretation (Gemini/OpenAI)
- **Modern Tooling**: Built with uv, ruff, and ty for enhanced development experience
- **Comprehensive Testing**: Unit and integration tests with coverage reporting
- **Security**: Input sanitization and prompt injection prevention
- **Observability**: Structured logging and performance monitoring

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) - Python package manager
- Redis (for conversation storage)
- Google Gemini API key (recommended) or OpenAI API key (for KnowledgeAgent and MathAgent)

## Quick Start

1. **Install uv** (if not already installed):
   ```bash
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # On Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Set up the development environment**:
   ```bash
   # Run the setup script
   python setup_venv.py
   
   # Or manually:
   uv sync --all-extras
   uv run pre-commit install
   ```

3. **Start the development server**:
   ```bash
   make run
   # or
   uv run uvicorn app.main:app --reload
   ```

## Development Workflow

### Available Commands

Use `make help` to see all available commands:

```bash
make help                # Show all available commands
make install-dev         # Install all dependencies
make test               # Run tests with coverage
make lint               # Run ruff linter
make format             # Format code with ruff
make type-check         # Run type checking with ty
make run                # Start development server
make check-all          # Run all checks (lint, format, type-check, test)
```

### Using uv Commands

```bash
# Install dependencies
uv sync --all-extras

# Run any command in the environment
uv run pytest
uv run ruff check .
uv run ty .

# Add new dependencies
uv add fastapi
uv add --dev pytest

# Remove dependencies
uv remove package-name
```

### Code Quality Tools

- **Ruff**: Fast Python linter and formatter (replaces flake8, black, isort)
- **Ty**: Enhanced type checking and validation
- **Pre-commit**: Automated code quality checks before commits

### Testing

```bash
# Run all tests
make test

# Run tests with watch mode
make test-watch

# Run specific test file
uv run pytest tests/test_models.py

# Run with coverage report
uv run pytest --cov=app --cov-report=html
```

### Linting and Formatting

```bash
# Check code style
make lint

# Auto-fix linting issues
make lint-fix

# Format code
make format

# Check formatting without changes
make format-check
```

### Type Checking

```bash
# Run type checking
make type-check

# Or directly with ty
uv run ty .
```

## Project Structure

```
backend/
├── app/                 # FastAPI application
│   ├── __init__.py
│   ├── main.py         # FastAPI app entry point
│   └── utils/          # Utility functions
├── agents/             # AI agents
│   ├── __init__.py
│   ├── base.py         # Base agent classes
│   ├── router_agent.py # Query routing logic
│   ├── math_agent.py   # Mathematical calculations (OpenAI)
│   ├── knowledge_agent.py # RAG-based responses (OpenAI)
│   ├── gemini_math_agent.py # Mathematical calculations (Gemini)
│   └── gemini_knowledge_agent.py # RAG-based responses (Gemini)
├── models/             # Data models
│   ├── __init__.py
│   └── core.py         # Pydantic models
├── services/           # External services
│   ├── __init__.py
│   └── redis_client.py # Redis connection
├── tests/              # Test suite
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_agents.py
│   └── test_api.py
├── pyproject.toml      # Project configuration
├── uv.lock            # Dependency lock file
├── Makefile           # Development commands
└── README.md          # This file
```

## Configuration

All configuration is managed through `pyproject.toml`:

- **Dependencies**: Production and development dependencies
- **Ruff**: Linting and formatting rules
- **Ty**: Type checking configuration
- **Pytest**: Test configuration and coverage settings

## Environment Variables

Create a `.env` file for local development:

```env
REDIS_URL=redis://localhost:6379
GEMINI_API_KEY=your_gemini_api_key        # Primary AI provider (recommended)
OPENAI_API_KEY=your_openai_api_key        # Fallback AI provider (optional)
LOG_LEVEL=INFO
CHROMA_PERSIST_DIR=./chroma_db
MAX_SCRAPE_PAGES=50
KNOWLEDGE_AGENT_TIMEOUT=30
```

## AI Provider Architecture

The system supports multiple AI providers with intelligent fallback:

### Gemini Agents (Primary)
- **GeminiMathAgent**: Uses Google Gemini 1.5 Flash for mathematical calculations
- **GeminiKnowledgeAgent**: Uses Google Gemini for RAG-based knowledge responses
- **Benefits**: Fast, cost-effective, high rate limits

### OpenAI Agents (Fallback)
- **MathAgent**: Uses OpenAI GPT-4 for mathematical calculations
- **KnowledgeAgent**: Uses OpenAI GPT-4 and text-embedding-ada-002 for RAG responses
- **Benefits**: Reliable backup, proven performance

### Selection Logic
1. Try Gemini agents first (if `GEMINI_API_KEY` is available)
2. Fall back to OpenAI agents (if `OPENAI_API_KEY` is available)
3. Use mock agents for testing (if no API keys are provided)

## KnowledgeAgent Details

The KnowledgeAgent (both Gemini and OpenAI versions) implements Retrieval-Augmented Generation (RAG) to provide accurate responses about InfinitePay services:

### Features
- **Web Scraping**: Automatically scrapes content from https://ajuda.infinitepay.io/pt-BR/
- **Vector Embeddings**: Uses Google Gemini (primary) or OpenAI embeddings (fallback) for semantic search
- **ChromaDB**: Persistent vector storage for efficient retrieval
- **Source Attribution**: Provides source URLs for generated responses
- **Intelligent Routing**: High confidence for InfinitePay-specific queries
- **AI Provider Fallback**: Automatically switches from Gemini to OpenAI if needed

### Configuration
- `CHROMA_PERSIST_DIR`: Directory for ChromaDB storage (default: ./chroma_db)
- `MAX_SCRAPE_PAGES`: Maximum pages to scrape (default: 50)
- `KNOWLEDGE_AGENT_TIMEOUT`: OpenAI API timeout in seconds (default: 30)

### Testing
```bash
# Test KnowledgeAgent integration
python test_knowledge_agent_integration.py

# Test in Docker environment
python test_knowledge_agent_docker.py
# or
./test_knowledge_agent_docker.ps1
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contributing

1. Install development dependencies: `make install-dev`
2. Install pre-commit hooks: `make pre-commit-install`
3. Make your changes
4. Run quality checks: `make check-all`
5. Commit your changes (pre-commit hooks will run automatically)

## Migration from requirements.txt

This project has been migrated from `requirements.txt` to `pyproject.toml` for better dependency management. The old `requirements.txt` file can be safely removed after verifying the migration is complete.

Key improvements:
- Dependency resolution and locking with uv
- Separate development and production dependencies
- Integrated tool configuration
- Better reproducible builds