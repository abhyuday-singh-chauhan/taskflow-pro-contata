from datetime import timedelta


def creates_cycle(graph, task_id, depends_on_task_id):
    """
    Check whether adding:

        task_id -> depends_on_task_id

    would create a cycle.
    """

    visited = set()

    def dfs(current):
        # If we reach the original task,
        # a cycle would be created.
        if current == task_id:
            return True

        # Already checked this task
        if current in visited:
            return False

        visited.add(current)

        # Check all dependencies of current task
        for dependency in graph.get(current, []):
            if dfs(dependency):
                return True

        return False

    return dfs(depends_on_task_id)


def get_task_state(task_id, task_status, dependencies):
    """
    Determine whether a task is READY or BLOCKED.

    A task is BLOCKED if any of its dependencies
    are not completed.

    A task is READY if all dependencies are done.
    """

    # No dependencies means the task is ready
    if task_id not in dependencies:
        return "READY"

    required_tasks = dependencies[task_id]

    for dependency_id in required_tasks:

        dependency_status = task_status.get(
            dependency_id
        )

        # If even one dependency is not done,
        # the task is blocked.
        if dependency_status != "done":
            return "BLOCKED"

    return "READY"


def calculate_schedule(
    task_id,
    graph,
    durations,
    start_date,
    memo=None
):
    """
    Calculate the earliest finish date for a task.

    graph:
        {
            task_id: [dependency_task_ids]
        }

    durations:
        {
            task_id: duration_in_days
        }

    start_date:
        Project start date

    memo:
        Stores already calculated results
        so the same task is not calculated repeatedly.
    """

    # Create memo dictionary if it doesn't exist
    if memo is None:
        memo = {}

    # If already calculated, return stored result
    if task_id in memo:
        return memo[task_id]

    # Get dependencies of this task
    dependencies = graph.get(task_id, [])

    # --------------------------------
    # No dependencies
    # --------------------------------
    if not dependencies:

        finish_date = (
            start_date
            + timedelta(days=durations[task_id])
        )

        memo[task_id] = finish_date

        return finish_date

    # --------------------------------
    # Find latest dependency finish
    # --------------------------------
    latest_finish = start_date

    for dependency_id in dependencies:

        dependency_finish = calculate_schedule(
            dependency_id,
            graph,
            durations,
            start_date,
            memo
        )

        if dependency_finish > latest_finish:
            latest_finish = dependency_finish

    # --------------------------------
    # Add current task duration
    # --------------------------------
    finish_date = (
        latest_finish
        + timedelta(days=durations[task_id])
    )

    memo[task_id] = finish_date

    return finish_date


def get_downstream_tasks(task_id, graph):
    """
    Find all tasks that depend directly or indirectly
    on the given task.

    Example:

        Task 1
        /    \
       Task 2 Task 3
          \   /
           Task 4

    If task_id = 1:
        returns {2, 3, 4}

    If task_id = 2:
        returns {4}
    """

    affected = set()

    def dfs(current_task):

        # Go through every task in the graph
        for task, dependencies in graph.items():

            # Check whether the current task
            # is a dependency of this task
            if current_task in dependencies:

                # Avoid processing the same task twice
                if task not in affected:

                    affected.add(task)

                    # Continue searching downstream
                    dfs(task)

    dfs(task_id)

    return affected