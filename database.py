import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "students.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # lets you access columns by name
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            student_id   TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            email        TEXT UNIQUE NOT NULL,
            interests    TEXT,
            home_location TEXT,
            grade        TEXT
        );

        CREATE TABLE IF NOT EXISTS courses (
            course_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT UNIQUE NOT NULL,
            domain       TEXT NOT NULL,
            term_years   REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS student_courses (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name       TEXT NOT NULL,
            course_name        TEXT NOT NULL,
            enrollment_start   TEXT NOT NULL,
            enrollment_end     TEXT,
            course_completed   INTEGER NOT NULL DEFAULT 0,
            UNIQUE(student_name, course_name)
        );
    """)
    conn.commit()
    conn.close()