from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase_auth.errors import AuthError

import db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    db.init_db()
    yield


app = FastAPI(lifespan=lifespan)
security = HTTPBearer(auto_error=False)


class Unauthorized(Exception):
    """Raised by the auth guard to short-circuit a protected route with a 401."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


@app.exception_handler(Unauthorized)
async def unauthorized_handler(request: Request, exc: Unauthorized) -> JSONResponse:
    return JSONResponse(status_code=401, content={"error": exc.message})


@app.get("/")
async def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": [
            "/",
            "/health",
            "/auth/signup",
            "/auth/login",
            "/tasks",
            "/tasks/{task_id}",
            "/stats",
            "/reset",
        ],
    }


@app.get("/tasks")
async def get_tasks(
    done: Optional[bool] = None, search: Optional[str] = None
) -> JSONResponse:
    conn = db.get_connection()
    cursor = conn.cursor()

    if not conn:
        return JSONResponse(
            status_code=500, content={"error": "Database connection failed"}
        )

    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if done is not None:
        query += f" AND done = %s"
        params.append(done)
    if search is not None:
        query += f" AND LOWER(title) LIKE %s"
        params.append(f"%{search.lower()}%")

    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return JSONResponse(status_code=200, content=results)


@app.get("/tasks/{task_id}")
async def get_task(task_id: int) -> JSONResponse:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    row = cursor.fetchone()
    conn.close()
    task = dict(row) if row else None
    if task:
        return JSONResponse(status_code=200, content=task)
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})


@app.get("/stats")
async def get_stats():
    conn = db.get_connection()
    if not conn:
        return JSONResponse(
            status_code=500, content={"error": "Database connection failed"}
        )

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE done = TRUE")
    done = cursor.fetchone()["count"]
    conn.close()
    return JSONResponse(
        status_code=200, content={"total": total, "done": done, "open": total - done}
    )


@app.post("/reset")
async def reset_tasks():
    conn = db.get_connection()
    if not conn:
        return JSONResponse(
            status_code=500, content={"error": "Database connection failed"}
        )

    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks")
    for task in db.seed_data:
        cursor.execute(
            "INSERT INTO tasks (id, title, done) VALUES (%s, %s, %s)",
            (task["id"], task["title"], task["done"]),
        )
    conn.commit()
    conn.close()
    return JSONResponse(
        status_code=200,
        content={"message": "Tasks reset to seed data", "count": len(db.seed_data)},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/signup")
async def signup(body: dict) -> JSONResponse:
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return JSONResponse(status_code=400, content={"error": "Bad Request"})

    try:
        res = db.supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
            }
        )
    except AuthError as e:
        return JSONResponse(status_code=400, content={"error": e.message})

    user = res.user.model_dump(mode="json") if res.user else None
    return JSONResponse(status_code=201, content=user)


@app.post("/auth/login")
async def login(body: dict) -> JSONResponse:
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return JSONResponse(status_code=400, content={"error": "Bad Request"})

    try:
        res = db.supabase.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )
    except AuthError:
        return JSONResponse(
            status_code=401, content={"error": "Invalid login credentials"}
        )

    return JSONResponse(
        status_code=200,
        content={
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
        },
    )


@app.post("/tasks")
async def create_task(task: dict) -> JSONResponse:
    conn = db.get_connection()
    cursor = conn.cursor()

    if task.get("title") is None:
        return JSONResponse(status_code=400, content={"error": "Title is required"})
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s)", (task["title"], False)
    )

    conn.commit()
    conn.close()
    return JSONResponse(
        status_code=201, content={"message": "Task created successfully"}
    )


@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: dict) -> JSONResponse:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    row = cursor.fetchall()[0]

    existing_task = dict(row) if row else None
    if existing_task is None:
        return JSONResponse(
            status_code=404, content={"error": f"Task {task_id} not found"}
        )
    if task.get("title") is None and task.get("done") is None:
        return JSONResponse(
            status_code=400, content={"error": "Title and done status are required"}
        )

    cursor.execute(
        "UPDATE tasks SET title = COALESCE(%s, title), done = COALESCE(%s, done) WHERE id = %s",
        (task.get("title"), task.get("done"), task_id),
    )
    conn.commit()
    conn.close()
    return JSONResponse(
        status_code=200, content={"message": f"Task {task_id} updated successfully"}
    )


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int) -> JSONResponse:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    row = cursor.fetchall()[0]

    existing_task = dict(row) if row else None
    if existing_task is None:
        return JSONResponse(
            status_code=404, content={"error": f"Task {task_id} not found"}
        )
    cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    conn.close()
    return Response(status_code=204)


@app.get("/public/info")
async def get_info() -> JSONResponse:
    return JSONResponse(
        status_code=200, content={"message": "Welcome stranger! This info is public."}
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """Reusable dependency guarding protected routes.

    Verifies the Bearer token from the Authorization header against Supabase,
    then returns the authenticated user's metadata so routes can use
    `user: dict = Depends(get_current_user)`. On any auth failure it raises
    Unauthorized, so the route body never runs for unauthenticated calls.
    """
    if not credentials:
        raise Unauthorized("token required")

    token = credentials.credentials
    # Ask Supabase whether the token is real. This is a network call, so the
    # answer is trustworthy (handles expiry, tampering, and invalid tokens).
    try:
        res = db.supabase.auth.get_user(token)
    except AuthError:
        raise Unauthorized("Invalid or expired token")

    if res is None or res.user is None:
        raise Unauthorized("Invalid or expired token")

    return res.user.model_dump(mode="json")


@app.get("/protected/profile")
async def get_profile(user: dict = Depends(get_current_user)) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "id": user.get("id"),
            "email": user.get("email"),
            "created_at": user.get("created_at"),
        },
    )


@app.post("/auth/logout")
async def logout(user: dict = Depends(get_current_user)) -> Response:
    # Guard already verified the token; now sign out on Supabase's side.
    db.supabase.auth.sign_out()
    return Response(status_code=204)


@app.get("/protected/dashboard")
async def get_dashboard(user: dict = Depends(get_current_user)) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "message": "Welcome to your dashboard!",
            "user_email": user.get("email"),
        },
    )
