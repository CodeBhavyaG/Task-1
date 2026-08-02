import sqlite3
import psycopg
import psycopg.rows
import dotenv
import os

dotenv.load_dotenv()

user = dotenv.get_key(".env", "POSTGRES_USER")
password = dotenv.get_key(".env", "POSTGRES_PASSWORD")

db_url = os.environ.get("DATABASE_URL", "postgres://postgres:dev@localhost:5432/tasks")


seed_data = [
    {"id": 1, "title": "Task 1", "done": False},
    {"id": 2, "title": "Task 2", "done": True},
    {"id": 3, "title": "Task 3", "done": False},
]


def get_connection() -> psycopg.Connection[psycopg.rows.DictRow] | None:
    try:
        conn = psycopg.connect(db_url, row_factory=psycopg.rows.dict_row)
        return conn
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None


def init_db():

    try:
        connection = psycopg.connect(db_url, row_factory=psycopg.rows.dict_row)
        cursor = connection.cursor()

        # Query the system master table for a specific table name
        table_name = "tasks"

        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                title TEXT,
                done BOOLEAN
            );
            """
        cursor.execute(create_table_query)
        connection.commit()
        print("Table 'tasks' created successfully (or already exists).")
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        print("Falling back to SQLite database.")

    # Fetch the result
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchall()[0]

    if row_count == 0:
        cursor.execute(f"DELETE FROM {table_name}")

    # Insert seed data
        for task in seed_data:
            cursor.execute(
                f"INSERT INTO {table_name} (id, title, done) VALUES ({task['id']}, '{task['title']}', {task['done']})"
            )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    init_db()
