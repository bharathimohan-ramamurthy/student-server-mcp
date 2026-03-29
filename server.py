from mcp.server.fastmcp import FastMCP
from database import get_connection, init_db
from seed_data import seed
import json
import uvicorn
from starlette.middleware.cors import CORSMiddleware

# Initialize DB on startup
init_db()
seed()

mcp = FastMCP("Student Records System")

# ─── Helper ─────────────────────────────────────────────────────────────────

def row_to_dict(row):
    return dict(row) if row else None


# ─── Student Tools ───────────────────────────────────────────────────────────

@mcp.tool()
def get_student(student_id: str) -> str:
    """Retrieve a student record by their Student ID."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM students WHERE student_id = ?", (student_id,)
    ).fetchone()
    conn.close()
    if row:
        return json.dumps(row_to_dict(row))
    return json.dumps({"error": f"No student found with ID '{student_id}'"})


@mcp.tool()
def add_student(
    student_id: str,
    name: str,
    email: str,
    interests: str,
    home_location: str,
    grade: str,
) -> str:
    """Add a new student to the system."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO students VALUES (?,?,?,?,?,?)",
            (student_id, name, email, interests, home_location, grade),
        )
        conn.commit()
        return json.dumps({"success": True, "message": f"Student '{name}' added."})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
    finally:
        conn.close()


@mcp.tool()
def search_student(query: str) -> str:
    """Search students by name, email, interests, or home location."""
    conn = get_connection()
    like = f"%{query}%"
    rows = conn.execute(
        """SELECT * FROM students
           WHERE name LIKE ? OR email LIKE ?
              OR interests LIKE ? OR home_location LIKE ?""",
        (like, like, like, like),
    ).fetchall()
    conn.close()
    results = [row_to_dict(r) for r in rows]
    return json.dumps(results if results else {"message": "No students matched."})


@mcp.tool()
def enroll_student(
    student_name: str,
    course_name: str,
    enrollment_start: str,
    enrollment_end: str = None,
) -> str:
    """Enroll a student in a course. enrollment_start format: YYYY-MM-DD."""
    conn = get_connection()
    # Verify student exists
    student = conn.execute(
        "SELECT name FROM students WHERE name = ?", (student_name,)
    ).fetchone()
    if not student:
        conn.close()
        return json.dumps({"success": False, "error": f"Student '{student_name}' not found."})

    # Verify course exists
    course = conn.execute(
        "SELECT name FROM courses WHERE name = ?", (course_name,)
    ).fetchone()
    if not course:
        conn.close()
        return json.dumps({"success": False, "error": f"Course '{course_name}' not found."})

    try:
        conn.execute(
            """INSERT INTO student_courses
               (student_name, course_name, enrollment_start, enrollment_end, course_completed)
               VALUES (?,?,?,?,0)""",
            (student_name, course_name, enrollment_start, enrollment_end),
        )
        conn.commit()
        return json.dumps({"success": True, "message": f"'{student_name}' enrolled in '{course_name}'."})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
    finally:
        conn.close()


# ─── Course Tools ─────────────────────────────────────────────────────────────

@mcp.tool()
def courses_available() -> str:
    """List all available courses."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM courses ORDER BY domain, name").fetchall()
    conn.close()
    return json.dumps([row_to_dict(r) for r in rows])


@mcp.tool()
def add_course(name: str, domain: str, term_years: float) -> str:
    """Add a new course. domain examples: technology, science, arts, business."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO courses (name, domain, term_years) VALUES (?,?,?)",
            (name, domain, term_years),
        )
        conn.commit()
        return json.dumps({"success": True, "message": f"Course '{name}' added."})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
    finally:
        conn.close()


@mcp.tool()
def search_course(query: str) -> str:
    """Search courses by name or domain."""
    conn = get_connection()
    like = f"%{query}%"
    rows = conn.execute(
        "SELECT * FROM courses WHERE name LIKE ? OR domain LIKE ?",
        (like, like),
    ).fetchall()
    conn.close()
    results = [row_to_dict(r) for r in rows]
    return json.dumps(results if results else {"message": "No courses matched."})


# ─── Entry point ─────────────────────────────────────────────────────────────

#if __name__ == "__main__":
#    mcp.run(transport="stdio")

if __name__ == "__main__":
    app = mcp.streamable_http_app()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    uvicorn.run(app, host="127.0.0.1", port=8000)
