from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from typing import Optional

SEED = [
    {"id": 1, "title": "Task 1", "done": False},
    {"id": 2, "title": "Task 2", "done": True},
    {"id": 3, "title": "Task 3", "done": False},
]

data = [dict(task) for task in SEED]

app = FastAPI()


@app.get("/")
async def root():
    return { "name": "Task API", "version": "1.0", "endpoints": ["/", "/health", "/tasks", "/tasks/{task_id}", "/stats", "/reset"] }


@app.get("/tasks")
async def get_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    results = data
    if done is not None:
        results = [task for task in results if task["done"] == done]
    if search:
        results = [task for task in results if search.lower() in task["title"].lower()]
    return results


@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    task = next((task for task in data if task["id"] == task_id), None)
    if task:
        return JSONResponse(status_code=200, content=task)
    return JSONResponse(status_code=404, content={ "error": f"Task {task_id} not found" })


@app.get("/stats")
async def get_stats():
    total = len(data)
    done = sum(1 for task in data if task["done"])
    return { "total": total, "done": done, "open": total - done }


@app.post("/reset")
async def reset_tasks():
    data[:] = [dict(task) for task in SEED]
    return JSONResponse(status_code=200, content={ "message": "Tasks reset to seed data", "count": len(data) })


@app.get("/health")
async def health():
    return { "status": "ok" }


@app.post("/tasks")
async def create_task(task: dict):
    new_id = len(data) + 1

    if task.get("title") is None:
        return JSONResponse(status_code=400, content={ "error": "Title is required" })
    data.append({"id": new_id, "title": task["title"], "done": task.get("done", False)})
    return JSONResponse(status_code=201, content={ "message": f"Task {new_id} created successfully" })


@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: dict):
    existing_task = next((t for t in data if t["id"] == task_id), None)
    if existing_task is None:
        return JSONResponse(status_code=404, content={ "error": f"Task {task_id} not found" })
    if task.get("title") is None and task.get("done") is None:
        return JSONResponse(status_code=400, content={ "error": "Title and done status are required" })

    existing_task.update(task)
    return JSONResponse(status_code=200, content={ "message": f"Task {task_id} updated successfully" })

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    existing_task = next((t for t in data if t["id"] == task_id), None)
    if existing_task is None:
        return JSONResponse(status_code=404, content={ "error": f"Task {task_id} not found" })
    data.remove(existing_task)
    return JSONResponse(status_code=200, content={ "message": f"Task {task_id} deleted successfully" })
