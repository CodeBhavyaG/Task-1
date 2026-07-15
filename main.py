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
    return { "name": "Task API", "version": "1.0", "endpoints": ["/", "/health"] }

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