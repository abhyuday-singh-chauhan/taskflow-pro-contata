from datetime import date

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
from models import Task, TaskDependency
from schemas import (
    TaskCreate,
    TaskUpdate,
    DependencyCreate,
    AISuggestionRequest
)
from ai_engine import suggest_dependencies
from dependency_engine import (
    creates_cycle,
    get_task_state,
    calculate_schedule,
    get_downstream_tasks
)


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI()


# -------------------------
# CORS
# -------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Database session
# -------------------------

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# -------------------------
# Home / Health Check
# -------------------------

@app.get("/") 
def home():
    return {
        "message": "TaskFlow Pro Backend is running"
    }


# -------------------------
# CREATE TASK
# POST /tasks
# -------------------------

@app.post("/tasks")
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db)
):
    new_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        start_date=task.start_date,
        end_date=task.end_date,
        position=task.position
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


# -------------------------
# GET ALL TASKS
# GET /tasks
# -------------------------

@app.get("/tasks") # when client send request to GET TASK
def get_tasks(
    db: Session = Depends(get_db) # this is session can ask from sqlite to give task
):
    tasks = db.query(Task).all() # This give all the matching task

    return tasks


# -------------------------
# UPDATE TASK
# PATCH /tasks/{task_id}
# -------------------------

@app.patch("/tasks/{task_id}")
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):
    # Find the task
    task = db.query(Task).filter(
        Task.id == task_id
    ).first()  # because before updating anything, the backend need to find the actual task

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    # Store old status before updating
    old_status = task.status

    # Get only fields that were actually sent
    update_data = task_data.model_dump(
        exclude_unset=True  # update only what user has provided does not automatically update all
    )

    # --------------------------------
    # WORKFLOW VALIDATION
    # --------------------------------

    if "status" in update_data:

        new_status = update_data["status"]

        # Allowed workflow order
        status_order = {
            "backlog": 0,
            "in_progress": 1,
            "review": 2,
            "done": 3
        }

        # Validate status name
        if new_status not in status_order:
            raise HTTPException(
                status_code=400,
                detail="Invalid task status"
            )

        if old_status not in status_order:
            raise HTTPException(
                status_code=400,
                detail="Invalid current task status"
            )

        old_position = status_order[old_status]
        new_position = status_order[new_status]

        # --------------------------------
        # PREVENT SKIPPING A STAGE
        # --------------------------------

        if new_position > old_position + 1:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Task must move through the workflow: "
                    f"{old_status} -> "
                    f"{list(status_order.keys())[old_position + 1]}"
                )
            )

        # --------------------------------
        # PREVENT MANUAL BACKWARD MOVEMENT
        # --------------------------------

        if new_position < old_position:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Tasks cannot be moved backward "
                    "through the workflow"
                )
            )

    # --------------------------------
    # UPDATE TASK
    # --------------------------------

    for key, value in update_data.items():
        setattr(task, key, value)

    # --------------------------------
    # ROLLBACK LOGIC
    # --------------------------------

    # Rollback is triggered when a task
    # moves from DONE to another status.
    #
    # This is automatic system behaviour,
    # not manual drag-and-drop movement.
    if (
        old_status == "done"
        and task.status != "done"
    ):

        # Get all dependency relationships
        dependency_rows = db.query(
            TaskDependency
        ).all()

        # Build dependency graph
        graph = {}

        for item in dependency_rows:

            if item.task_id not in graph:
                graph[item.task_id] = []

            graph[item.task_id].append(
                item.depends_on_task_id
            )

        # Find all downstream tasks
        affected_tasks = get_downstream_tasks( #to check task is affected downstream
            task_id,
            graph
        )

        # Roll back completed downstream tasks
        # here it check task one by one
        for affected_task_id in affected_tasks:

            affected_task = db.query(Task).filter( # than retrive the actual task
                Task.id == affected_task_id
            ).first()

            if affected_task and affected_task.status == "done":
                affected_task.status = "in_progress"

    # Save changes
    db.commit()

    # Refresh main task
    db.refresh(task)

    return task


# -------------------------
# DELETE TASK
# DELETE /tasks/{task_id}
# -------------------------

@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(
        Task.id == task_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    # Delete all dependencies connected to this task.
    #
    # task_id = task that depends on another task
    #
    # depends_on_task_id = prerequisite task
    #
    # Remove both cases so no orphan
    # dependency records remain.
    db.query(TaskDependency).filter(
        (TaskDependency.task_id == task_id) |
        (TaskDependency.depends_on_task_id == task_id)
    ).delete(
        synchronize_session=False
    )

    # Delete task
    db.delete(task)

    db.commit()

    return {
        "message": "Task deleted successfully"
    }


# -------------------------
# ADD TASK DEPENDENCY
# POST /tasks/{task_id}/dependencies
# -------------------------

@app.post("/tasks/{task_id}/dependencies")
def add_dependency(
    task_id: int,
    dependency: DependencyCreate,
    db: Session = Depends(get_db)
):
    # Check main task exists
    task = db.query(Task).filter(
        Task.id == task_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    # Check dependency task exists
    depends_on_task = db.query(Task).filter(
        Task.id == dependency.depends_on_task_id
    ).first()

    if not depends_on_task:
        raise HTTPException(
            status_code=404,
            detail="Dependency task not found"
        )

    # Task cannot depend on itself
    if task_id == dependency.depends_on_task_id:
        raise HTTPException(
            status_code=400,
            detail="A task cannot depend on itself"
        )

    # Check duplicate dependency
    existing = db.query(TaskDependency).filter(
        TaskDependency.task_id == task_id,
        TaskDependency.depends_on_task_id ==
        dependency.depends_on_task_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Dependency already exists"
        )

    # Build dependency graph
    dependencies = db.query(TaskDependency).all()

    graph = {}

    for item in dependencies:

        if item.task_id not in graph:
            graph[item.task_id] = []

        graph[item.task_id].append(
            item.depends_on_task_id
        )

    # Check for cycle
    if creates_cycle(
        graph,
        task_id,
        dependency.depends_on_task_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Dependency would create a cycle"
        )

    # Save dependency
    new_dependency = TaskDependency(
        task_id=task_id,
        depends_on_task_id=dependency.depends_on_task_id
    )

    db.add(new_dependency)
    db.commit()
    db.refresh(new_dependency)

    return new_dependency


# -------------------------
# GET TASK DEPENDENCIES
# GET /tasks/{task_id}/dependencies
# -------------------------

@app.get("/tasks/{task_id}/dependencies")
def get_dependencies(
    task_id: int,
    db: Session = Depends(get_db)
):
    # Check task exists
    task = db.query(Task).filter(
        Task.id == task_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    dependencies = db.query(TaskDependency).filter(
        TaskDependency.task_id == task_id
    ).all()

    return dependencies


# -------------------------
# DELETE TASK DEPENDENCY
# DELETE /tasks/{task_id}/dependencies/{dependency_id}
# -------------------------

@app.delete(
    "/tasks/{task_id}/dependencies/{dependency_id}"
)
def delete_dependency(
    task_id: int,
    dependency_id: int,
    db: Session = Depends(get_db)
):
    dependency = db.query(TaskDependency).filter(
        TaskDependency.id == dependency_id,
        TaskDependency.task_id == task_id
    ).first()

    if not dependency:
        raise HTTPException(
            status_code=404,
            detail="Dependency not found"
        )

    db.delete(dependency)
    db.commit()

    return {
        "message": "Dependency deleted successfully"
    }


# -------------------------
# GET TASK STATE
# GET /tasks/{task_id}/state
# -------------------------

@app.get("/tasks/{task_id}/state")
def get_task_state_api(
    task_id: int,
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(
        Task.id == task_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    tasks = db.query(Task).all()

    task_status = {
        item.id: item.status
        for item in tasks
    }

    dependency_rows = db.query(
        TaskDependency
    ).all()

    dependencies = {}

    for item in dependency_rows:

        if item.task_id not in dependencies:
            dependencies[item.task_id] = []

        dependencies[item.task_id].append(
            item.depends_on_task_id
        )

    state = get_task_state(
        task_id,
        task_status,
        dependencies
    )

    return {
        "task_id": task_id,
        "status": task.status,
        "state": state
    }


# -------------------------
# CALCULATE TASK SCHEDULE
# GET /tasks/{task_id}/schedule
# -------------------------

@app.get("/tasks/{task_id}/schedule")
def get_task_schedule(
    task_id: int,
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(
        Task.id == task_id
    ).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    tasks = db.query(Task).all()

    dependency_rows = db.query(
        TaskDependency
    ).all()

    graph = {}

    for item in dependency_rows:

        if item.task_id not in graph:
            graph[item.task_id] = []

        graph[item.task_id].append(
            item.depends_on_task_id
        )

    durations = {}

    project_start = None

    for item in tasks:

        if not item.start_date or not item.end_date:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Task {item.id} must have "
                    "start_date and end_date"
                )
            )

        try:
            task_start = date.fromisoformat(
                item.start_date
            )

            task_end = date.fromisoformat(
                item.end_date
            )

        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid date format for "
                    f"task {item.id}. Use YYYY-MM-DD"
                )
            )

        if task_end < task_start:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Task {item.id} has an end date "
                    "before its start date"
                )
            )

        duration = (
            task_end - task_start
        ).days

        durations[item.id] = duration

        if project_start is None:
            project_start = task_start

        elif task_start < project_start:
            project_start = task_start

    finish_date = calculate_schedule(
        task_id=task_id,
        graph=graph,
        durations=durations,
        start_date=project_start
    )

    return {
        "task_id": task_id,
        "earliest_finish": finish_date.isoformat()
    }


# -------------------------
# AI DEPENDENCY SUGGESTION
# POST /ai/suggest-dependencies
# -------------------------

@app.post("/ai/suggest-dependencies")
def ai_suggest_dependencies(
    request: AISuggestionRequest,
    db: Session = Depends(get_db)
):
    try:

        # Get all existing tasks
        existing_tasks = db.query(Task).all()

        # Ask AI engine for suggestions
        suggestions = suggest_dependencies(
            {
                "title": request.title,
                "description": request.description
            },
            existing_tasks
        )

        return {
            "new_task": request.title,
            "suggestions": suggestions
        }

    except Exception as e:

        # Print real error in FastAPI terminal
        print("AI ERROR:", repr(e))

        # Return readable error
        raise HTTPException(
            status_code=500,
            detail=f"AI suggestion failed: {str(e)}"
        )
