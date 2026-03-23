from database import get_connection, init_db

STUDENTS = [
    ("STU001", "Alice Chen",    "alice@example.com",  "AI, Robotics",       "San Francisco, CA", "A"),
    ("STU002", "Bob Martin",    "bob@example.com",    "Web Dev, Design",    "Austin, TX",        "B+"),
    ("STU003", "Clara Osei",    "clara@example.com",  "Biology, Chemistry", "London, UK",        "A-"),
    ("STU004", "David Kim",     "david@example.com",  "Music, Arts",        "Seoul, South Korea","B"),
    ("STU005", "Eva Rossi",     "eva@example.com",    "Physics, Math",      "Rome, Italy",       "A+"),
]

COURSES = [
    ("Machine Learning 101",  "technology", 1.0),
    ("Web Development Bootcamp", "technology", 0.5),
    ("Biology Fundamentals",  "science",    2.0),
    ("Art History",           "arts",       1.0),
    ("Quantum Physics",       "science",    2.0),
    ("Digital Marketing",     "business",   0.5),
    ("Music Theory",          "arts",       1.5),
    ("Data Structures",       "technology", 1.0),
]

ENROLLMENTS = [
    ("Alice Chen",  "Machine Learning 101",     "2024-01-15", "2025-01-15", 1),
    ("Alice Chen",  "Data Structures",           "2024-06-01", None,         0),
    ("Bob Martin",  "Web Development Bootcamp",  "2024-03-01", "2024-09-01", 1),
    ("Clara Osei",  "Biology Fundamentals",      "2024-02-01", None,         0),
    ("David Kim",   "Music Theory",              "2024-04-01", None,         0),
    ("Eva Rossi",   "Quantum Physics",           "2024-01-01", None,         0),
]

def seed():
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.executemany(
        "INSERT OR IGNORE INTO students VALUES (?,?,?,?,?,?)", STUDENTS
    )
    cur.executemany(
        "INSERT OR IGNORE INTO courses (name, domain, term_years) VALUES (?,?,?)", COURSES
    )
    cur.executemany(
        """INSERT OR IGNORE INTO student_courses
           (student_name, course_name, enrollment_start, enrollment_end, course_completed)
           VALUES (?,?,?,?,?)""",
        ENROLLMENTS
    )
    conn.commit()
    conn.close()
    print("Database seeded successfully.")

if __name__ == "__main__":
    seed()