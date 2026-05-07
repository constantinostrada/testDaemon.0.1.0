# Mini-Library API

A production-ready REST API and web frontend for managing a personal book library, built with **FastAPI** (Python backend) and **Next.js** (TypeScript frontend), following strict **Clean Architecture** principles.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Clean Architecture Layers](#clean-architecture-layers)
- [Getting Started](#getting-started)
  - [Backend Setup (FastAPI)](#backend-setup-fastapi)
  - [Frontend Setup (Next.js)](#frontend-setup-nextjs)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Running Tests](#running-tests)
- [Linting & Formatting](#linting--formatting)

---

## Overview

Mini-Library API lets you catalogue books, track reading status, and query your collection through a clean REST API. The frontend provides a simple UI powered by Next.js with TypeScript.

---

## Tech Stack

| Layer      | Technology                  |
|------------|-----------------------------|
| Backend    | Python 3.11+, FastAPI       |
| Frontend   | Next.js 14, TypeScript      |
| Database   | SQLite (via aiosqlite)      |
| Validation | Pydantic v2                 |
| Linting    | Ruff (Python), ESLint (TS)  |
| Formatting | Black (Python), Prettier    |
| Testing    | Pytest, Jest                |

---

## Project Structure

```
mini-library-api/
├── src/
│   ├── domain/               # Entities, Value Objects, Repository Interfaces
│   │   ├── entities/
│   │   ├── value_objects/
│   │   ├── repositories/
│   │   └── services/
│   ├── application/          # Use Cases, DTOs, Application Services
│   │   ├── use_cases/
│   │   ├── dtos/
│   │   └── ports/
│   ├── infrastructure/       # DB clients, ORM, external adapters
│   │   ├── database/
│   │   └── repositories/
│   └── interfaces/           # FastAPI routes, Next.js pages
│       ├── api/
│       │   ├── controllers/
│       │   └── main.py
│       └── web/              # Next.js frontend
│           ├── app/
│           ├── components/
│           └── lib/
├── tests/
│   ├── unit/
│   └── integration/
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Clean Architecture Layers

This project enforces the **Dependency Rule**: source-code dependencies point **inward only**.

```
interfaces → application → domain
infrastructure → application → domain
```

### `src/domain/` — The Core
The heart of the application. Contains all business rules with **zero external dependencies**.
- **Entities**: `Book` — has identity, protects invariants (ISBN format, non-empty title).
- **Value Objects**: `ISBN`, `BookStatus` — immutable, equality by value.
- **Repository Interfaces**: `BookRepository` — defines *what* operations exist, not *how*.
- **Domain Services**: `BookAvailabilityService` — logic that spans multiple entities.

### `src/application/` — Use Cases
Orchestrates domain objects to fulfill user stories. Knows *what* to do, not *how*.
- **Use Cases**: `AddBookUseCase`, `GetBookUseCase`, `ListBooksUseCase`, `UpdateBookStatusUseCase`, `DeleteBookUseCase` — each is a single class with an `execute(dto)` method.
- **DTOs**: Plain data contracts for input/output — no domain entities leak out.
- **Ports**: Abstractions (interfaces) for infrastructure services the application needs.

### `src/infrastructure/` — I/O Implementations
Implements interfaces defined in domain/application. All I/O lives here.
- **Database**: Async SQLite client via `aiosqlite`.
- **Repository Implementations**: `SQLiteBookRepository` maps DB rows ↔ domain entities.

### `src/interfaces/` — Entry Points
Thin adapters that translate HTTP ↔ use cases.
- **FastAPI Controllers**: Validate HTTP input → call use case → serialize DTO to JSON response.
- **Next.js Frontend**: React pages and components that consume the API.

---

## Getting Started

### Backend Setup (FastAPI)

**Prerequisites**: Python 3.11+, `pip`

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment variables
cp .env.example .env

# 4. Run the development server
uvicorn src.interfaces.api.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### Frontend Setup (Next.js)

**Prerequisites**: Node.js 18+, npm

```bash
# From the web directory
cd src/interfaces/web

# 1. Install dependencies
npm install

# 2. Copy environment variables
cp .env.local.example .env.local

# 3. Run the development server
npm run dev
```

The frontend will be available at `http://localhost:3000`.

---

## Environment Variables

See `.env.example` for all available variables.

| Variable         | Default              | Description                      |
|------------------|----------------------|----------------------------------|
| `DATABASE_URL`   | `./library.db`       | Path to SQLite database file     |
| `CORS_ORIGINS`   | `http://localhost:3000` | Allowed CORS origins          |
| `APP_ENV`        | `development`        | Environment name                 |
| `LOG_LEVEL`      | `info`               | Logging verbosity                |

---

## API Endpoints

| Method | Path                     | Description              |
|--------|--------------------------|--------------------------|
| GET    | `/health`                | Health check             |
| POST   | `/api/v1/books`          | Add a new book           |
| GET    | `/api/v1/books`          | List all books           |
| GET    | `/api/v1/books/{id}`     | Get a book by ID         |
| PATCH  | `/api/v1/books/{id}/status` | Update reading status |
| DELETE | `/api/v1/books/{id}`     | Delete a book            |

---

## Running Tests

```bash
# Python tests
pytest tests/ -v

# Python tests with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Frontend tests
cd src/interfaces/web && npm test
```

---

## Linting & Formatting

```bash
# Python — lint
ruff check src/ tests/

# Python — format
black src/ tests/

# Python — type check
mypy src/

# Frontend — lint
cd src/interfaces/web && npm run lint

# Frontend — format
cd src/interfaces/web && npm run format
```
