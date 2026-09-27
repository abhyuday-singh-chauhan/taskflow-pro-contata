from datetime import date, timedelta

from dependency_engine import calculate_schedule


# Diamond dependency graph
#
#        1
#       / \
#      2   3
#       \ /
#        4

graph = {
    2: [1],
    3: [1],
    4: [2, 3]
}


# Duration of each task in days
durations = {
    1: 2,
    2: 3,
    3: 5,
    4: 2
}


# Project starts on September 25
start_date = date(2026, 9, 25)


# Calculate Task 4 finish date
finish_date = calculate_schedule(
    task_id=4,
    graph=graph,
    durations=durations,
    start_date=start_date
)


print("Task 4 finish date:", finish_date)