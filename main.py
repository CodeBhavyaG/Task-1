from fastapi import FastAPI
from fastapi.responses import JSONResponse

data = [
    {"id": 1, "title": "Task 1", "done": False},
    {"id": 2, "title": "Task 2", "done": True},
    {"id": 3, "title": "Task 3", "done": False}
]

app = FastAPI()


@app.get("/")
async def root():
    return { "name": "Task API", "version": "1.0", "endpoints": ["/", "/health", "/tasks", "/tasks/{task_id}"] }

@app.get("/tasks")
async def get_tasks():
    return data

@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    task = next((task for task in data if task["id"] == task_id), None)
    if task:
        return JSONResponse(status_code=200, content=task)
    return JSONResponse(status_code=404, content={ "error": f"Task {task_id} not found" }) 

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
