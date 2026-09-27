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



