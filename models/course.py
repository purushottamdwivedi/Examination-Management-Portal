"""courses table."""
from database import query, execute

def create(code, name, description, credits, status):
    return execute('INSERT INTO courses(code,name,description,credits,status) VALUES(?,?,?,?,?)',
                   (code, name, description, credits or 0, status))

def get(cid):
    return query('SELECT * FROM courses WHERE id=?', (cid,), True)

def all():
    return query('SELECT * FROM courses ORDER BY id DESC')

def active():
    return query("SELECT * FROM courses WHERE status='Active'")

def update(cid, code, name, description, credits, status):
    execute('UPDATE courses SET code=?,name=?,description=?,credits=?,status=? WHERE id=?',
            (code, name, description, credits or 0, status, cid))

def has_exams(cid):
    return bool(query('SELECT 1 FROM exams WHERE course_id=?', (cid,)))

def delete(cid):
    execute('DELETE FROM courses WHERE id=?', (cid,))

def count():
    return query('SELECT COUNT(*) c FROM courses', one=True)['c']
