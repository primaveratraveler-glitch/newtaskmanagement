from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, date
from flask import session

app = Flask(__name__)
app.secret_key = "secret-key-for-danger-alert"


def get_db_connection():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    return conn

def judge_alert(task):
    if not task["due_date"]:
        return None

    due = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
    today = date.today()
    days_left = (due - today).days

    if days_left < 0:
        return "danger"      # 期限切れ
    elif days_left <= 3:
        return "danger"
    elif days_left <= 7:
        return "warning"
    else:
        return None

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    conn = get_db_connection()

    task = conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    if task is None:
        conn.close()
        return "Task not found", 404

    if request.method == "POST":
        title = request.form["title"]
        due_date = request.form["due_date"]

        conn.execute(
            "UPDATE tasks SET title = ?, due_date = ? WHERE id = ?",
            (title, due_date, task_id)
        )
        conn.commit()
        conn.close()
        return redirect("/")

    conn.close()
    return render_template("edit.html", task=task)





@app.route("/")
def index():
    conn = get_db_connection()
    tasks = conn.execute("""
        SELECT * FROM tasks
        ORDER BY due_date IS NULL, due_date ASC
    """).fetchall()
    conn.close()

    tasks_with_alert = []
    has_danger = False

    for task in tasks:
        task = dict(task)

        # 完了タスクは判定しない
        if task["status"] == "done":
            task["alert_level"] = None
        else:
            task["alert_level"] = judge_alert(task)

        if task["alert_level"] == "danger":
            has_danger = True

        tasks_with_alert.append(task)

    return render_template(
        "index.html",
        tasks=tasks_with_alert,
        has_danger=has_danger
    )



@app.route("/add_form")
def add_form():
    return render_template("add.html")

@app.route("/add", methods=["POST"])
def add_task():
    title = request.form["title"]
    due_date = request.form["due_date"]

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO tasks (title, status, due_date)
        VALUES (?, ?, ?)
        """,
        (title, "todo", due_date)
    )
    conn.commit()
    conn.close()

    return redirect("/")



@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    conn = get_db_connection()
    conn.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )
    conn.commit()
    conn.close()
    return redirect("/")



if __name__ == "__main__":
    app.run(debug=True)
