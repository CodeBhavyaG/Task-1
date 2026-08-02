# Task API

A simple RESTful API for managing tasks built with FastAPI and PostgreSQL. This API provides full CRUD (Create, Read, Update, Delete) operations for a task list with persistent storage.

## Quick Start with Docker Compose (Recommended)

```bash
# Clone and run
docker-compose up --build
```

The API will be available at `http://localhost:8000`.

**What happens automatically:**
- PostgreSQL database started in a container
- API server started with uv
- Dependencies installed (`fastapi`, `uvicorn`, `psycopg`)
- Database initialized with 3 seed tasks
- Health checks ensure database is ready before API starts

## Local Development (without Docker)

```bash
# Start PostgreSQL locally (or use existing instance)
# Update .env with your DATABASE_URL

# Install dependencies and run
uv run uvicorn api:app --reload
```

The API will be available at `http://localhost:8000`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with API information |
| GET | `/health` | Health check endpoint |
| GET | `/tasks` | Retrieve all tasks (supports `?done=true|false` and `?search=<text>` filters) |
| GET | `/tasks/{task_id}` | Retrieve a specific task by ID |
| POST | `/tasks` | Create a new task (JSON: `{"title": "string", "done": false}`) |
| PUT | `/tasks/{task_id}` | Update an existing task (JSON: `{"title": "string"}` and/or `{"done": boolean}`) |
| DELETE | `/tasks/{task_id}` | Delete a task |
| GET | `/stats` | Return counts: `{"total": N, "done": N, "open": N}` |
| POST | `/reset` | Restore the original 3 seed tasks (wipes all changes) |

## Example Usage

```bash
# List all tasks
curl http://localhost:8000/tasks

# Filter by completion status
curl "http://localhost:8000/tasks?done=false"

# Search by title
curl "http://localhost:8000/tasks?search=task"

# Get a single task
curl http://localhost:8000/tasks/1

# Create a task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "New task", "done": false}'

# Update a task (partial updates supported)
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"done": true}'

# Delete a task
curl -X DELETE http://localhost:8000/tasks/1

# Get stats
curl http://localhost:8000/stats

# Reset to seed data
curl -X POST http://localhost:8000/reset
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
Task-1/
├── api.py              # FastAPI routes & business logic
├── db.py               # PostgreSQL connection & initialization
├── docker-compose.yml  # Docker Compose configuration
├── Dockerfile          # Docker image definition
├── pyproject.toml      # Project metadata & dependencies
├── uv.lock             # Locked dependencies
├── .env                # Environment variables
└── README.md           # This file
```

## Development

This project uses:
- FastAPI 0.139+
- Uvicorn 0.51+
- psycopg 3.3+
- Python 3.12+
- UV for package management

Dependencies are managed with UV and can be found in `pyproject.toml`.

### Run with auto-reload (development)

```bash
uv run uvicorn api:app --reload
```

## Persistence

Tasks are stored in a PostgreSQL database, so they **survive server restarts**. The database is initialized automatically on first run with three seed tasks:

1. Task 1 — not done
2. Task 2 — done
3. Task 3 — not done

Use `POST /reset` to restore this initial state.

## Configuration

Environment variables (in `.env`):
- `POSTGRES_USER` - Database username
- `POSTGRES_PASSWORD` - Database password
- `DATABASE_URL` - Full PostgreSQL connection string