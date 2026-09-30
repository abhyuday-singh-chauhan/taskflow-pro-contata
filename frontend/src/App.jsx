import { useState, useEffect } from "react";  // usestate allow react component to store info that can change over time
import "./App.css";

function App() {

  console.log("NEW APP.JSX IS RUNNING");

  // settask does not change the UI it chamge the react state
  
  const [tasks, setTasks] = useState([]); // settask use to change // task which is given

  const [showForm, setShowForm] = useState(false);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  // State used for editing an existing task
  const [editingTaskId, setEditingTaskId] = useState(null); // useeffect, run the code when specific data change
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState(""); // loadtask, it load the task automatically the UI Page
  const [editStatus, setEditStatus] = useState("backlog");

  // Stores the ID of the task currently being dragged
  const [draggedTaskId, setDraggedTaskId] = useState(null);

  // Stores the ID of the task whose dependencies we are managing
  const [dependencyTaskId, setDependencyTaskId] = useState(null);

  // Stores the IDs selected as dependencies
  const [selectedDependencies, setSelectedDependencies] = useState([]);

  // Stores READY / BLOCKED state of each task
  const [taskStates, setTaskStates] = useState({});

  // --------------------------------
  // AI DEPENDENCY SUGGESTIONS
  // --------------------------------

  // Stores AI suggested dependencies
  const [aiSuggestions, setAiSuggestions] = useState([]);

  // Shows whether Gemini is currently generating suggestions
  const [aiLoading, setAiLoading] = useState(false);

  // Stores AI errors
  const [aiError, setAiError] = useState("");

  const columns = [
    {
      id: "backlog",
      title: "Backlog"
    },
    {
      id: "in_progress",
      title: "In Progress"
    },
    {
      id: "review",
      title: "Review"
    },
    {
      id: "done",
      title: "Done"
    }
  ];


  // --------------------------------
  // FETCH TASK STATE
  // --------------------------------

  async function fetchTaskState(taskId) {

    try {

      const response = await fetch(
        `http://127.0.0.1:8000/tasks/${taskId}/state`
      );

      if (!response.ok) {

        throw new Error(
          "Failed to fetch task state"
        );

      }

      const data =
        await response.json();

      setTaskStates((currentStates) => ({
        ...currentStates,
        [taskId]: data.state
      }));

    } catch (error) {

      console.error(
        "Error fetching task state:",
        error
      );

    }
  }


  // --------------------------------
  // LOAD TASKS
  // --------------------------------

  useEffect(() => {

    console.log("Calling FastAPI...");

    fetch("http://127.0.0.1:8000/tasks")

      .then((response) => {

        console.log(
          "Response status:",
          response.status
        );

        if (!response.ok) {

          throw new Error(
            "Backend returned an error"
          );

        }

        return response.json();

      })

      .then((data) => {

        console.log(
          "REAL DATABASE TASKS:",
          data
        );

        setTasks(data);

        // Fetch READY / BLOCKED state
        // for every task
        data.forEach((task) => {
          fetchTaskState(task.id);
        });

      })

      .catch((error) => {

        console.error(
          "FETCH ERROR:",
          error
        );

      });

  }, []);


  // --------------------------------
  // CREATE TASK
  // --------------------------------

  async function handleSubmit(event) {

    event.preventDefault();

    if (title.trim() === "") {
      return;
    }

    try {

      const response = await fetch(
        "http://127.0.0.1:8000/tasks",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json"
          },

          body: JSON.stringify({
            title: title,
            description: description,
            status: "backlog"
          })
        }
      );

      if (!response.ok) {

        throw new Error(
          "Failed to create task"
        );

      }

      const createdTask =
        await response.json();

      setTasks((currentTasks) => [
        ...currentTasks,
        createdTask
      ]);

      // Fetch state for newly created task
      fetchTaskState(createdTask.id);

      setTitle("");
      setDescription("");
      setShowForm(false);

    } catch (error) {

      console.error(
        "Error creating task:",
        error
      );

    }
  }


  // --------------------------------
  // EDIT TASK
  // --------------------------------

  async function handleEditSubmit(event) {

    event.preventDefault();

    try {

      const response = await fetch(
        `http://127.0.0.1:8000/tasks/${editingTaskId}`,
        {
          method: "PATCH",

          headers: {
            "Content-Type": "application/json"
          },

          body: JSON.stringify({
            title: editTitle,
            description: editDescription,
            status: editStatus
          })
        }
      );

      if (!response.ok) {

        throw new Error(
          "Failed to update task"
        );

      }

      // The backend can change downstream tasks
      // when rollback logic is triggered.
      //
      // Therefore, reload the complete task list
      // instead of updating only the edited task.

      const tasksResponse = await fetch(
        "http://127.0.0.1:8000/tasks"
      );

      if (!tasksResponse.ok) {

        throw new Error(
          "Failed to refresh tasks"
        );

      }

      const latestTasks =
        await tasksResponse.json();

      setTasks(latestTasks);

      // Refresh READY / BLOCKED state
      // for every task.
      latestTasks.forEach((task) => {
        fetchTaskState(task.id);
      });

      setEditingTaskId(null);

    } catch (error) {

      console.error(
        "Error updating task:",
        error
      );

    }
  }


  // --------------------------------
  // DELETE TASK
  // --------------------------------

  async function handleDelete(taskId) {

    try {

      const response = await fetch(
        `http://127.0.0.1:8000/tasks/${taskId}`,
        {
          method: "DELETE"
        }
      );

      if (!response.ok) {

        throw new Error(
          "Failed to delete task"
        );

      }

      setTasks((currentTasks) =>
        currentTasks.filter(
          (task) => task.id !== taskId
        )
      );

      // Remove deleted task from state storage
      setTaskStates((currentStates) => {

        const updatedStates = {
          ...currentStates
        };

        delete updatedStates[taskId];

        return updatedStates;

      });

    } catch (error) {

      console.error(
        "Error deleting task:",
        error
      );

    }
  }


  // --------------------------------
  // DRAG AND DROP
  // --------------------------------

  async function handleDrop(status) {

    if (draggedTaskId === null) {
      return;
    }

    console.log(
      "Task dropped:",
      draggedTaskId,
      "New status:",
      status
    );

    try {

      const response = await fetch(
        `http://127.0.0.1:8000/tasks/${draggedTaskId}`,
        {
          method: "PATCH",

          headers: {
            "Content-Type": "application/json"
          },

          body: JSON.stringify({
            status: status
          })
        }
      );

      if (!response.ok) {

        throw new Error(
          "Failed to update task status"
        );

      }

      // The backend may have changed multiple tasks
      // because of rollback logic.
      //
      // Reload the complete task list so the
      // frontend matches the database.

      const tasksResponse = await fetch(
        "http://127.0.0.1:8000/tasks"
      );

      if (!tasksResponse.ok) {

        throw new Error(
          "Failed to refresh tasks"
        );

      }

      const latestTasks =
        await tasksResponse.json();

      setTasks(latestTasks);

      // Refresh READY / BLOCKED state
      // for every task.
      latestTasks.forEach((task) => {
        fetchTaskState(task.id);
      });

      setDraggedTaskId(null);

    } catch (error) {

      console.error(
        "Error updating task status:",
        error
      );

    }
  }


  // --------------------------------
  // SELECT / UNSELECT DEPENDENCY
  // --------------------------------

  function handleDependencyChange(taskId) {

    setSelectedDependencies((current) => {

      // If task is already selected,
      // remove it.
      if (current.includes(taskId)) {

        return current.filter(
          (id) => id !== taskId
        );

      }

      // Otherwise add the task ID.
      return [
        ...current,
        taskId
      ];

    });

  }


  // --------------------------------
  // ADD DEPENDENCIES
  // --------------------------------

  async function handleAddDependencies() {

    if (dependencyTaskId === null) {
      return;
    }

    if (selectedDependencies.length === 0) {

      alert(
        "Please select at least one dependency."
      );

      return;
    }

    try {

      // Send every selected dependency
      // to the FastAPI backend.
      for (
        const dependencyId
        of selectedDependencies
      ) {

        const response = await fetch(
          `http://127.0.0.1:8000/tasks/${dependencyTaskId}/dependencies`,
          {
            method: "POST",

            headers: {
              "Content-Type": "application/json"
            },

            body: JSON.stringify({
              depends_on_task_id:
                dependencyId
            })
          }
        );

        const data =
          await response.json();

        console.log("AI RESPONSE:", data);

        if (!response.ok) {

          throw new Error(
            data.detail ||
            "Failed to add dependency"
          );

        }

      }

      alert(
        "Dependencies added successfully!"
      );

      console.log(
        "Saved dependencies:",
        selectedDependencies
      );

      // Refresh the task state because
      // adding a dependency can make
      // a task BLOCKED.
      fetchTaskState(dependencyTaskId);

      // Clear selected dependencies
      setSelectedDependencies([]);

      // Close dependency panel
      setDependencyTaskId(null);

    } catch (error) {

      console.error(
        "Error adding dependencies:",
        error
      );

      alert(
        error.message
      );

    }
  }


  // --------------------------------
  // AI: SUGGEST DEPENDENCIES
  // --------------------------------

  async function handleAISuggestions(task) {

    setAiLoading(true);
    setAiError("");
    setAiSuggestions([]);

    try {

      const response = await fetch(
        "http://127.0.0.1:8000/ai/suggest-dependencies",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json"
          },

          body: JSON.stringify({
            title: task.title,
            description: task.description || ""
          })
        }
      );

      const data =
        await response.json();

      if (!response.ok) {

        throw new Error(
          data.detail ||
          "Failed to get AI suggestions"
        );

      }

      /*
        Gemini returns task IDs.

        We convert those IDs into complete task
        objects so that the frontend can display
        the actual task title.
      */

      const suggestionsWithTasks =
        data.suggestions

          .map((suggestion) => {

            const suggestedTask =
              tasks.find(
                (existingTask) =>
                  existingTask.id ===
                  suggestion.task_id
              );

            if (!suggestedTask) {
              return null;
            }

            return {
              ...suggestion,
              task: suggestedTask
            };

          })

          .filter(
            (suggestion) =>
              suggestion !== null &&
              suggestion.task.id !== task.id
          );

      setAiSuggestions(
        suggestionsWithTasks
      );

    } catch (error) {

      console.error(
        "AI suggestion error:",
        error
      );

      setAiError(
        error.message ||
        "Unable to get AI suggestions."
      );

    } finally {

      setAiLoading(false);

    }
  }


  // --------------------------------
  // ACCEPT AI SUGGESTION
  // --------------------------------

  async function handleAcceptAISuggestion(
    taskId,
    dependencyId
  ) {

    try {

      const response = await fetch(
        `http://127.0.0.1:8000/tasks/${taskId}/dependencies`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json"
          },

          body: JSON.stringify({
            depends_on_task_id:
              dependencyId
          })
        }
      );

      const data =
        await response.json();

      if (!response.ok) {

        throw new Error(
          data.detail ||
          "Failed to add AI suggested dependency"
        );

      }

      alert(
        "AI suggestion accepted and dependency added!"
      );

      // Refresh task state
      fetchTaskState(taskId);

      // Remove accepted suggestion
      setAiSuggestions((currentSuggestions) =>
        currentSuggestions.filter(
          (suggestion) =>
            suggestion.task.id !== dependencyId
        )
      );

    } catch (error) {

      console.error(
        "Error accepting AI suggestion:",
        error
      );

      alert(
        error.message
      );

    }
  }


  // --------------------------------
  // REJECT AI SUGGESTION
  // --------------------------------

  function handleRejectAISuggestion(
    dependencyId
  ) {

    setAiSuggestions((currentSuggestions) =>
      currentSuggestions.filter(
        (suggestion) =>
          suggestion.task.id !== dependencyId
      )
    );

  }


  // --------------------------------
  // UI
  // --------------------------------

  return (

    <div className="app">

      {/* HEADER */}

      <div className="header">

        <h1>
          TaskFlow Pro
        </h1>

        <p>
          AI-powered project management
          with dependency intelligence
        </p>

        <button
          onClick={() =>
            setShowForm(!showForm)
          }
        >
          + Create Task
        </button>

      </div>


      {/* CREATE TASK FORM */}

      {showForm && (

        <form
          onSubmit={handleSubmit}
          className="task-form"
        >

          <input
            type="text"
            placeholder="Task title"
            value={title}
            onChange={(event) =>
              setTitle(
                event.target.value
              )
            }
          />

          <textarea
            placeholder="Task description"
            value={description}
            onChange={(event) =>
              setDescription(
                event.target.value
              )
            }
          />

          <button type="submit">
            Create Task
          </button>

        </form>

      )}


      {/* KANBAN BOARD */}

      <div className="board">

        {columns.map((column) => (

          <div
            className="column"
            key={column.id}

            onDragOver={(event) =>
              event.preventDefault()
            }

            onDrop={() =>
              handleDrop(column.id)
            }
          >

            <h2>
              {column.title}
            </h2>


            {/* TASKS IN THIS COLUMN */}

            {tasks

              .filter(
                (task) =>
                  task.status === column.id
              )

              .map((task) => (

                <div
                  className="task-card"
                  key={task.id}

                  draggable={true}

                  onDragStart={() =>
                    setDraggedTaskId(
                      task.id
                    )
                  }
                >

                  <h3>
                      #{task.id} {task.title}
                  </h3>

                  <p>
                    {task.description}
                  </p>


                  {/* READY / BLOCKED STATE */}

                  <p>
                    State:{" "}
                    {
                      taskStates[task.id] ||
                      "Checking..."
                    }
                  </p>


                  {/* EDIT BUTTON */}

                  <button
                    onClick={() => {

                      setEditingTaskId(
                        task.id
                      );

                      setEditTitle(
                        task.title
                      );

                      setEditDescription(
                        task.description || ""
                      );

                      setEditStatus(
                        task.status
                      );

                    }}
                  >
                    Edit
                  </button>


                  {/* DELETE BUTTON */}

                  <button
                    onClick={() =>
                      handleDelete(
                        task.id
                      )
                    }
                  >
                    Delete
                  </button>


                  {/* DEPENDENCY BUTTON */}

                  <button
                    onClick={() => {

                      setDependencyTaskId(
                        task.id
                      );

                      // Clear old selections
                      setSelectedDependencies([]);

                      // Clear previous AI results
                      setAiSuggestions([]);

                      setAiError("");

                    }}
                  >
                    Dependencies
                  </button>


                  {/* --------------------------------
                      DEPENDENCY PANEL
                      -------------------------------- */}

                  {dependencyTaskId === task.id && (

                    <div
                      className="dependency-panel"
                    >

                      <h4>
                        Dependencies
                      </h4>

                      <p>
                        Select the tasks that
                        must be completed before
                        this task.
                      </p>


                      {/* SHOW OTHER TASKS */}

                      {tasks

                        .filter(
                          (otherTask) =>
                            otherTask.id !==
                            task.id
                        )

                        .map((otherTask) => (

                          <label
                            key={otherTask.id}

                            style={{
                              display: "block",
                              marginBottom: "8px"
                            }}
                          >

                            <input
                              type="checkbox"

                              checked={selectedDependencies.includes(
                                otherTask.id
                              )}

                              onChange={() =>
                                handleDependencyChange(
                                  otherTask.id
                                )
                              }
                            />

                            {" "}

                            {otherTask.title}

                          </label>

                        ))
                      }


                      {/* NUMBER SELECTED */}

                      <p>
                        Selected:{" "}
                        {
                          selectedDependencies.length
                        }
                      </p>


                      {/* ADD DEPENDENCIES */}

                      <button
                        type="button"

                        onClick={
                          handleAddDependencies
                        }
                      >
                        Add Dependencies
                      </button>


                      {/* --------------------------------
                          AI SUGGESTION BUTTON
                          -------------------------------- */}

                      <button
                        type="button"

                        onClick={() =>
                          handleAISuggestions(task)
                        }

                        disabled={aiLoading}
                      >
                        {aiLoading
                          ? "AI Thinking..."
                          : "Suggest with AI"}
                      </button>


                      {/* --------------------------------
                          AI ERROR
                          -------------------------------- */}

                      {aiError && (

                        <p
                          style={{
                            color: "#dc2626",
                            fontWeight: "600"
                          }}
                        >
                          {aiError}
                        </p>

                      )}


                      {/* --------------------------------
                          AI SUGGESTIONS
                          -------------------------------- */}

                      {aiSuggestions.length > 0 && (

                        <div className="ai-suggestions">

                          <h4>
                            AI Suggestions
                          </h4>

                          <p>
                            Gemini identified these
                            tasks as likely prerequisites.
                          </p>


                          {aiSuggestions.map(
                            (suggestion) => (

                              <div
                                className="ai-suggestion"
                                key={
                                  suggestion.task.id
                                }
                              >

                                <strong>
                                  {suggestion.task.title}
                                </strong>

                                <p>
                                  {suggestion.reason}
                                </p>

                                <p>
                                  Confidence:{" "}
                                  {Math.round(
                                    suggestion.confidence *
                                    100
                                  )}
                                  %
                                </p>


                                {/* ACCEPT */}

                                <button
                                  type="button"

                                  onClick={() =>
                                    handleAcceptAISuggestion(
                                      task.id,
                                      suggestion.task.id
                                    )
                                  }
                                >
                                  Accept
                                </button>


                                {/* REJECT */}

                                <button
                                  type="button"

                                  onClick={() =>
                                    handleRejectAISuggestion(
                                      suggestion.task.id
                                    )
                                  }
                                >
                                  Reject
                                </button>

                              </div>

                            )
                          )}

                        </div>

                      )}


                      {/* NO SUGGESTIONS */}

                      {!aiLoading &&
                        !aiError &&
                        aiSuggestions.length === 0 && (

                          <p>
                            No AI suggestions yet.
                          </p>

                        )
                      }


                      {/* CLOSE */}

                      <button
                        type="button"

                        onClick={() => {

                          setDependencyTaskId(
                            null
                          );

                          setSelectedDependencies([]);

                          setAiSuggestions([]);

                          setAiError("");

                        }}
                      >
                        Close
                      </button>

                    </div>

                  )}


                  {/* --------------------------------
                      EDIT FORM
                      -------------------------------- */}

                  {editingTaskId === task.id && (

                    <form
                      onSubmit={
                        handleEditSubmit
                      }

                      className="task-form"
                    >

                      <input
                        type="text"
                        value={editTitle}

                        onChange={(event) =>
                          setEditTitle(
                            event.target.value
                          )
                        }
                      />


                      <textarea
                        value={
                          editDescription
                        }

                        onChange={(event) =>
                          setEditDescription(
                            event.target.value
                          )
                        }
                      />


                      <select
                        value={editStatus}

                        onChange={(event) =>
                          setEditStatus(
                            event.target.value
                          )
                        }
                      >

                        <option value="backlog">
                          Backlog
                        </option>

                        <option value="in_progress">
                          In Progress
                        </option>

                        <option value="review">
                          Review
                        </option>

                        <option value="done">
                          Done
                        </option>

                      </select>


                      <button type="submit">
                        Save Changes
                      </button>


                      <button
                        type="button"

                        onClick={() =>
                          setEditingTaskId(
                            null
                          )
                        }
                      >
                        Cancel
                      </button>

                    </form>

                  )}

                </div>

              ))
            }

          </div>

        ))}

      </div>

    </div>

  );

}

export default App;
