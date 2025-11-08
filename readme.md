# SQL DB Demo with public employees database: Modular FastAPI + SQLAlchemy + MariaDB Architecture

This project is an educational yet production-grade example of SQL database access implemented within a two-tier front-end / back-end architecture.

At its core, it demonstrates how data persistence (SQL), business logic (Python/FastAPI), and user interaction (HTML/JavaScript) can coexist in a cleanly separated and composable system — the standard design pattern in modern web and data engineering.

## 1. Overview

The Core Concept: Front-End vs. Back-End

| **Layer** | **Technology** | **Role** | **Example in This Project** |
|------------|----------------|-----------|------------------------------|
| **Front-End** | HTML + JavaScript | User interface that runs in the browser. It sends HTTP requests to the API and renders the results dynamically. | `frontend/index.html` |
| **Back-End** | FastAPI (Python) + SQLAlchemy | Application server that handles requests, queries the SQL database, and returns structured JSON data. | `backend/main.py` and `app/` modules |
| **Database** | MariaDB / MySQL | Persistent storage containing the `employees` data schema. | `employees` database from [datacharmer/test_db](https://github.com/datacharmer/test_db) |


This project demonstrates a **fully decoupled three-layer backend architecture** for database-centric web applications built on:

- **FastAPI** (for asynchronous, typed, API orchestration)
- **SQLAlchemy 2.x** (for declarative ORM and database abstraction)
- **MariaDB/MySQL** (for relational persistence)
- **Pydantic v2** (for strict schema validation and data interchange)

It exposes a minimal RESTful API that reads from the canonical [`employees`](https://github.com/datacharmer/test_db) database, retrieving the first 10 employee names. 
It is functionally simple, but the structure embodies a scalable pattern used in industrial, scientific, and enterprise systems.

---

## 2. Architectural Philosophy

The design adheres to **clean architecture** and **separation of concerns**. 
Each Python module has a sharply delimited responsibility that aligns with one of the canonical layers:

| Layer | Responsibility | Directory/Module |
|--------|----------------|------------------|
| **Interface Layer (API)** | Request routing, HTTP semantics, validation, serialization | `main.py`, `app/routers/` |
| **Application Layer (Service / CRUD)** | Business logic, orchestration of persistence operations | `app/crud.py` |
| **Domain Layer (Schema / Models)** | Entity representation (DB and API), domain contracts | `app/models.py`, `app/schemas.py` |
| **Infrastructure Layer** | Database connectivity, configuration, environment management | `app/db.py`, `app/config.py`, `app/deps.py` |

The result is an *inversion-tolerant* codebase: each layer depends only on abstractions or upward contracts, not on concrete downstream implementations.

---

## 3. Module-by-Module Deep Dive

### `main.py` — **Application Entry Point**

- Creates and configures the **FastAPI application object**. 
- Installs **CORS middleware** (necessary for local or cross-origin frontends). 
- Registers routers that declare actual API endpoints.
- Acts as the **composition root** of the dependency graph — no logic, only wiring.

**Design principle:** *composition over inheritance*. The root application composes independent subsystems.

---

### `app/config.py` — **Configuration Management**

- Centralized environment and runtime configuration loader.
- Uses `.env` via `python-dotenv` for runtime configurability.
- Defines the immutable `Settings` object (a `pydantic.BaseModel`) containing:
  - DB connection parameters
  - CORS policies (Cross-Origin Resource Sharing - a security mechanism that allows a web browser to request resources from a different origin than the one that served the page)
  - Other tunables, at deploy-time 

**Philosophy:** *Configuration as data.* 
By modeling configuration with Pydantic, validation, introspection, and serialization become "first-class citizens".

---

### `app/db.py` — **Database Engine Factory**

- Constructs the **SQLAlchemy engine** using the dynamic DSN assembled from `config.py`.
- Defines the **SessionLocal** factory (thread-safe `sessionmaker`).
- Declares `Base` as a subclass of `DeclarativeBase`, the metaclass root for ORM models.

**Principle:** *Explicit session boundaries and stateless engine.* 
The engine is shared, but sessions are short-lived and context-managed, preventing transactional bleed or concurrency hazards.

---

### `app/models.py` — **Database Domain Models**

- Defines ORM entities that map directly to physical database tables. 
- Here: `Employee`, mapping to the `employees` table.
- Type-annotated attributes (PEP 484) feed both static typing and SQLAlchemy’s new declarative syntax.

**Philosophy:** *Data models should describe, not manipulate.* 
Models express *structure and semantics* of persisted data, leaving orchestration to the CRUD layer.

---

### `app/schemas.py` — **Serialization and Validation Contracts**

- Contains Pydantic models representing the **public interface** (API I/O).
- The schema decouples internal ORM objects from external JSON payloads.
- Ensures only whitelisted, serializable fields are exposed to clients.

**Principle:** *Never expose ORM entities directly.* 
Pydantic enforces data integrity at the API boundary and guards against overexposure.

---

### `app/crud.py` — **Application Logic (CRUD Services - Create, Read, Update, and Delete)**

- Encapsulates read/write operations in reusable service functions.
- Implements one pure function: `get_employees()`, which performs a `SELECT` query returning first/last names.

**Philosophy:** *Functional thin services.* 
CRUD functions are stateless, deterministic, and fully testable; they may evolve into a Service or Repository layer in large systems.

---

### `app/deps.py` — **Dependency Injection Utilities**

DI - Dependency Injection - a design principle and software pattern where instead of a component creating or owning the objects it needs, those objects are provided (injected) to it from the outside.
In other words, dependencies are declared, not constructed inside the component.

- Defines reusable dependency providers for FastAPI.
- `get_db()` yields a session and ensures it is closed after request completion.

**Principle:** *Contextual resource management via DI.* 

By abstracting DB sessions into dependencies, endpoint handlers remain pure and easily testable.

---

### `app/routers/employees.py` — **Endpoint Router**

- Declares `/employees` endpoint under its own **APIRouter**.
- Binds query parameters (`limit`, `offset`) and injects the DB session dependency.
- Converts SQLAlchemy row objects into `EmployeeOut` Pydantic models.

**Philosophy:** *Routers = interface boundary of the bounded context.* 
Each router forms a micro-module representing a cohesive domain service (e.g., employees, departments, titles).

---

### `app/routers/__init__.py`

- Lightweight package initializer that re-exports router modules.
- Supports future expansion (`departments.py`, `titles.py`, etc.) without touching the root composition.

**Design principle:** *Open/Closed principle.* 
Adding new domain routers does not require modifying core code, only registration in `main.py`.

---

## 4. Systemic Relationships

NOTE: Object Relational Mapping (ORM) is a technique used in creating a bridge between object-oriented programs and, in most cases, relational databases.

```
HTTP Request
   │
   ▼
FastAPI Router (/employees)
   │ (Depends → get_db)
   ▼
CRUD Layer (get_employees)
   │
   ▼
SQLAlchemy Session  ←─── Declarative ORM Models
   │
   ▼
MariaDB Storage Engine
```

Upstream data flow (response path):

```
MariaDB Row → ORM Object → CRUD Function → Pydantic Schema → JSON Response
```

This **bidirectional data transformation** ensures isolation between database schema evolution and API contract stability.

---

## 5. Design Principles & Philosophical Foundations

| Concept | Explanation |
|----------|--------------|
| **Layered Architecture** | Each layer has a single responsibility: configuration, data access, domain, application logic, or API exposure. |
| **Dependency Inversion** | Higher layers depend on abstractions (`get_db`, `BaseModel`) not concrete implementations. |
| **Explicit Resource Ownership** | Database sessions are context-managed, preventing leaks or hidden side effects. |
| **Type Safety as Design Constraint** | Typing informs both static checks and runtime validation; contracts are self-documenting. |
| **Composability** | Routers are composable; services are stateless; the architecture is horizontally scalable. |
| **Configurability via Environment** | No hardcoded paths or secrets; runtime tunables drive the system. |
| **Minimal Coupling to Framework** | Only `main.py` and routers depend on FastAPI; business logic and models remain portable to other frameworks (Flask, Starlette, etc.). |

---

## 6. Evolution and Scalability

The same architecture trivially scales to production:

- Add `alembic/` for migrations.
- Introduce `tests/` with `pytest` fixtures for isolated DB sessions.
- Implement `departments`, `titles`, or `salaries` routers.
- Replace `PyMySQL` with any other SQLAlchemy dialect (PostgreSQL, SQLite) by adjusting one environment variable.

Because **each concern is encapsulated**, the codebase remains *evolution-ready* without architectural refactoring.

---

## 7. Frontend Integration

The minimal `frontend/index.html` acts as an external consumer of the REST API. 
This is intentional: the API layer is *network-transparent*, meaning it can support a static web client, a React SPA, or another service.

---

## 8. Summary

This project exemplifies **clarity by construction**:

> “Every module should be understandable in isolation yet composable in context.”

By enforcing strong separation, explicit dependencies, and minimal cross-layer leakage, it achieves the holy trinity of academic software design: 
**extensibility, testability, and epistemic transparency.**
