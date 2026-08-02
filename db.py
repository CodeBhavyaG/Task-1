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

        create_table_query = """
            CREATE TABLE IF NOT EXISTS tasks (
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
        connection = None
        cursor = None

    if connection is not None and cursor is not None:
        # Fetch the result
        try:
            cursor.execute("SELECT COUNT(*) FROM tasks")
            row_count = cursor.fetchall()[0]

            # Only insert seed data if table is empty
            if row_count == 0:
                # Insert seed data using parameterized queries
                for task in seed_data:
                    cursor.execute(
                        "INSERT INTO tasks (id, title, done) VALUES (%s, %s, %s)",
                        (task['id'], task['title'], task['done'])
                    )
                connection.commit()
                print("Seed data inserted successfully.")
            else:
                print("Database already contains data, skipping seed insertion.")

            connection.close()
        except Exception as e:
            print(f"Error during database operations: {e}")
            if not connection.closed:
                connection.close()


if __name__ == "__main__":
    init_db()
