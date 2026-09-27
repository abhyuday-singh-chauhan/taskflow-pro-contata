# TASKFLOW PRO

TaskFlow Pro is a dependency-aware project management system built around a simple Kanban board.

At first glance, it looks like a normal task management application with columns such as **Backlog, In Progress, Review, and Done**. The main idea behind the project, however, is what happens underneath those columns.

Instead of treating tasks as independent items, TaskFlow Pro understands the relationships between them.

For example:

Database Schema → Backend API → Integration Testing

If the Database Schema is not completed, the system can identify that the Backend API is blocked. If a dependency changes later, the system can also identify the downstream tasks affected by that change.

The project combines a React frontend, FastAPI backend, SQLite database, a DAG-based dependency engine, schedule calculation, rollback handling, and AI-assisted dependency suggestions.

---

## WHY I BUILT THIS

A simple Kanban board tells you **what state a task is in**.

It does not necessarily tell you:

- Which tasks are blocking it?
- Can this task actually start?
- Would adding this dependency create a cycle?
- What happens to downstream work if a prerequisite becomes incomplete?
- What is the earliest time a dependent task can finish?
- Which existing tasks might be prerequisites for a newly created task?

TaskFlow Pro was designed to address these problems.

The goal was not to build another basic CRUD application, but to make the task board understand **task dependencies and their consequences**.

---

## KEY FEATURES

### 1. Kanban Task Management

Tasks are organized into four workflow stages:

```text
Backlog → In Progress → Review → Done
