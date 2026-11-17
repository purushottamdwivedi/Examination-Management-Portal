"""Database layer: connection helpers + table creation (schema is created in code)."""
import sqlite3
from flask import g
from werkzeug.security import generate_password_hash
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, role TEXT NOT NULL, name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, phone TEXT, department TEXT, student_no TEXT,
  status TEXT DEFAULT 'approved', created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS courses(id INTEGER PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
  description TEXT, credits INTEGER DEFAULT 0, status TEXT DEFAULT 'Active');
CREATE TABLE IF NOT EXISTS exams(id INTEGER PRIMARY KEY, course_id INTEGER NOT NULL REFERENCES courses(id),
  name TEXT NOT NULL, type TEXT NOT NULL, duration INTEGER, max_marks INTEGER NOT NULL,
  sc_start TEXT, sc_end TEXT, bk_start TEXT, bk_end TEXT, venue TEXT,
  status TEXT DEFAULT 'Draft', published INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS exam_examiners(exam_id INTEGER REFERENCES exams(id), examiner_id INTEGER REFERENCES users(id),
  PRIMARY KEY(exam_id, examiner_id));
CREATE TABLE IF NOT EXISTS rubrics(id INTEGER PRIMARY KEY, exam_id INTEGER NOT NULL REFERENCES exams(id),
  name TEXT NOT NULL, max_marks REAL NOT NULL, weight REAL NOT NULL, description TEXT);
CREATE TABLE IF NOT EXISTS slots(id INTEGER PRIMARY KEY, exam_id INTEGER NOT NULL REFERENCES exams(id),
  examiner_id INTEGER NOT NULL REFERENCES users(id), date TEXT NOT NULL, start TEXT NOT NULL, end TEXT NOT NULL,
  capacity INTEGER NOT NULL, available INTEGER NOT NULL, status TEXT DEFAULT 'Available', location TEXT);
CREATE TABLE IF NOT EXISTS bookings(id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL REFERENCES users(id),
  slot_id INTEGER NOT NULL REFERENCES slots(id), exam_id INTEGER NOT NULL REFERENCES exams(id),
  booked_on TEXT DEFAULT CURRENT_TIMESTAMP, status TEXT DEFAULT 'Booked');
CREATE TABLE IF NOT EXISTS evaluations(booking_id INTEGER REFERENCES bookings(id), rubric_id INTEGER REFERENCES rubrics(id),
  marks REAL, PRIMARY KEY(booking_id, rubric_id));
CREATE TABLE IF NOT EXISTS results(booking_id INTEGER PRIMARY KEY REFERENCES bookings(id), total REAL, remarks TEXT,
  evaluated_on TEXT DEFAULT CURRENT_TIMESTAMP);
"""

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db

def close_db(e=None):
    d = g.pop('db', None)
    if d:
        d.close()

def query(sql, args=(), one=False):
    """SELECT helper. one=True returns a single row (or None)."""
    rows = get_db().execute(sql, args).fetchall()
    return (rows[0] if rows else None) if one else rows

def execute(sql, args=()):
    """INSERT/UPDATE/DELETE helper. Returns the new row id."""
    cur = get_db().execute(sql, args)
    get_db().commit()
    return cur.lastrowid

def init_db():
    """Create all tables and the pre-existing Admin account."""
    c = sqlite3.connect(DB_PATH)
    c.executescript(SCHEMA)
    if not c.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
        c.execute("INSERT INTO users(role,name,email,password) VALUES('admin','Administrator','admin@emp.com',?)",
                  (generate_password_hash('admin123'),))
    c.commit(); c.close()
