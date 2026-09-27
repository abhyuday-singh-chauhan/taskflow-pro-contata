import os
import time
from google import genai

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def suggest_dependencies(new_task, existing_tasks):
    """
    Ask Gemini to suggest which existing tasks
    should be dependencies of a new task.
    """

    task_information = []

    for task in existing_tasks:
        task_information.append(
            f"ID: {task.id}, "
            f"Title: {task.title}, "
            f"Description: {task.description or 'No description'}"
        )

    existing_tasks_text = "\n".join(task_information)

    prompt = f"""
You are an AI assistant for a project management system.

We have a new task:

Title: {new_task["title"]}
Description: {new_task.get("description") or "No description"}

Here are the existing tasks:

{existing_tasks_text}

Identify which existing tasks are likely prerequisites
(dependencies) for the new task.

Return ONLY the IDs of tasks that are genuine prerequisites,
as a comma-separated list.

If there are no suitable dependencies, return:
NONE

Do not invent task IDs.
"""

    # Try Gemini up to 3 times because temporary
    # 503 errors can occur when the model is busy.
    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            result = response.text.strip()

            if result.upper() == "NONE":
                return []

            suggestions = []

            valid_ids = {task.id for task in existing_tasks}

            for value in result.split(","):

                value = value.strip()

                try:
                    task_id = int(value)

                    if task_id in valid_ids:
                        suggestions.append({
                            "task_id": task_id,
                            "reason": (
                                "Gemini identified this task "
                                "as a likely prerequisite."
                            ),
                            "confidence": 0.85
                        })

                except ValueError:
                    continue

            return suggestions

        except Exception as e:

            # If Gemini temporarily fails,
            # wait before trying again.
            if attempt < 2:
                time.sleep(2)
            else:
                raise e