import sqlite3

seed_data = [
    {"id": 1, "title": "Task 1", "done": False},
    {"id": 2, "title": "Task 2", "done": True},
    {"id": 3, "title": "Task 3", "done": False},
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    connection = sqlite3.connect("tasks.db")
    cursor = connection.cursor()

    # Query the system master table for a specific table name
    table_name = "task"
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )

    # Fetch the result
    if not cursor.fetchone():
        # Table does not exist, create it
        print(f"Table '{table_name}' does not exist. Creating the table.")
        cursor.execute(
            """
            CREATE TABLE task (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL CHECK (done IN (0, 1))
            )
            """
        )

    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]

    if row_count == 0:
        cursor.execute(f"DELETE FROM {table_name}")
        # Insert seed data
        for task in seed_data:
            cursor.execute(
                "INSERT INTO task (id, title, done) VALUES (?, ?, ?)",
                (task["id"], task["title"], task["done"])
            )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    init_db()
