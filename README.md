# TaskFlow Pro

TaskFlow Pro is a dependency-aware project management system built around a Kanban board.

The main idea behind the project is simple: managing tasks by status is not enough when tasks depend on each other.

For example:

Database Schema → Backend API → Integration Testing

If the database task is not completed, the backend task should not be considered ready. Similarly, if an upstream task changes, the system should be able to identify which downstream tasks are affected.

TaskFlow Pro combines a Kanban workflow with dependency management, DAG-based validation, dependency-aware scheduling, automatic rollback, persistent storage, and AI-assisted dependency suggestions.

---

## Why I Built This

Most basic Kanban applications mainly focus on moving tasks between columns such as:

Backlog → In Progress → Review → Done

While this is useful, real projects usually have dependencies between tasks.

For example:

- Backend API depends on the database schema.
- Frontend integration depends on the backend API.
- Integration testing depends on both frontend and backend.
- A task may become blocked if one of its prerequisites is incomplete.

I wanted to build a project management system where these relationships are actually understood by the application instead of being treated as simple labels.

That is the main reason TaskFlow Pro uses a dependency engine in addition to the Kanban board.

---

# Key Features

## 1. Kanban Task Management

The application provides four workflow stages:

- Backlog
- In Progress
- Review
- Done

Tasks can be created, updated, deleted and moved through the workflow.

The workflow is intentionally controlled so that tasks cannot simply jump from:

Backlog → Done

Instead, they follow:

Backlog → In Progress → Review → Done

This keeps the workflow predictable and makes the task lifecycle easier to reason about.

---

## 2. Drag and Drop

Tasks can be moved between Kanban columns using drag and drop.

When a task is moved, the frontend sends the updated status to the FastAPI backend.

The backend validates the transition before updating the database.

The status is therefore not only changed visually on the frontend; it is persisted in the database.

---

## 3. Persistent Database

TaskFlow Pro uses SQLite for local persistence.

The database stores information such as:

- Task ID
- Title
- Description
- Status
- Start date
- End date
- Position
- Creation timestamp

Task dependencies are stored separately.

This means that refreshing the application does not remove the tasks or their relationships.

---

## 4. Dependency Management

A task can depend on one or more other tasks.

For example:


Task 1: Database Schema
        ↓
Task 2: Backend API
        ↓
Task 3: Integration Testing


# 5. AI Architecture

New Task
   ↓
React Frontend
   ↓
FastAPI
   ↓
AI Engine
   ↓
Google Gemini
   ↓
Suggested Dependencies
   ↓
User Accept / Reject
   ↓
Backend Validation
   ↓
Dependency Database

# 6. Technology Stack
Frontend
React
Vite
JavaScript
CSS
HTML5 Drag and Drop API

The frontend is responsible for the user interface and communicating with the backend APIs.

Backend
Python
FastAPI
SQLAlchemy
Pydantic

FastAPI provides the REST API layer.

Pydantic is used for request validation and structured API data.

SQLAlchemy is used to communicate with the database.

Database
SQLite

SQLite was chosen because it is lightweight and simple to run locally without requiring a separate database server.

The database layer is designed so that the storage system can be replaced by a larger relational database such as PostgreSQL in a production deployment.

AI
Google Gemini
Google GenAI Python SDK

Gemini is used for suggesting possible task dependencies based on task titles and descriptions.

The final dependency graph is still controlled by deterministic backend validation.

# 7. Backend work

Backend Files
main.py

Contains the FastAPI application and API endpoints.

It handles operations such as:

Creating tasks
Reading tasks
Updating tasks
Deleting tasks
Adding dependencies
Removing dependencies
Checking task state
Calculating schedules
Requesting AI suggestions

It also handles validation and database transactions.

database.py

Contains the SQLAlchemy database configuration.

It creates the SQLite database connection and provides the SQLAlchemy base and session configuration.

models.py

Contains the database models.

The main models are:

Task
TaskDependency

Task stores task information.

TaskDependency stores the relationship between a task and the task it depends on.

schemas.py

Contains Pydantic request schemas used to validate API input.

Examples include:

TaskCreate
TaskUpdate
DependencyCreate
AISuggestionRequest
dependency_engine.py

This is one of the most important files in the project.

It contains the core dependency logic including:

Cycle detection
READY/BLOCKED state calculation
Schedule calculation
Downstream task detection

Keeping this logic separate from the API layer makes the dependency system easier to test and maintain.

ai_engine.py

Contains the Gemini integration.

It:

Builds the context of existing tasks.
Sends the new task and existing task information to Gemini.
Parses the response.
Filters invalid task IDs.
Returns structured dependency suggestions.


# 8. API Overview

Some of the main API endpoints are:

Method	Endpoint	Purpose
GET	/	Check backend status
POST	/tasks	Create a task
GET	/tasks	Get all tasks
PATCH	/tasks/{id}	Update a task
DELETE	/tasks/{id}	Delete a task
POST	/tasks/{id}/dependencies	Add dependency
GET	/tasks/{id}/dependencies	Get dependencies
DELETE	/tasks/{id}/dependencies/{dependency_id}	Remove dependency
GET	/tasks/{id}/state	Get READY/BLOCKED state
GET	/tasks/{id}/schedule	Calculate schedule
POST	/ai/suggest-dependencies	Get AI dependency suggestions

FastAPI also provides interactive API documentation through Swagger.



