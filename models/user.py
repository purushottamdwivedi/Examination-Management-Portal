"""users table: admin, examiner (profile + approval status) and student accounts."""
from database import query, execute

def create(role, name, email, password_hash, phone=None, department=None, student_no=None, status='approved'):
    return execute('INSERT INTO users(role,name,email,password,phone,department,student_no,status) VALUES(?,?,?,?,?,?,?,?)',
                   (role, name, email, password_hash, phone, department, student_no, status))

def get(uid):
    return query('SELECT * FROM users WHERE id=?', (uid,), True)

def get_by_email(email):
    return query('SELECT * FROM users WHERE email=?', (email,), True)

def list_by_role(role):
    return query('SELECT * FROM users WHERE role=? ORDER BY id DESC', (role,))

def pending_examiners():
    return query("SELECT * FROM users WHERE role='examiner' AND status='pending'")

def count(role):
    return query('SELECT COUNT(*) c FROM users WHERE role=?', (role,), True)['c']

def update_profile(uid, name, phone, department, student_no):
    execute('UPDATE users SET name=?, phone=?, department=?, student_no=? WHERE id=?',
            (name, phone, department, student_no, uid))

def update_password(uid, password_hash):
    execute('UPDATE users SET password=? WHERE id=?', (password_hash, uid))

def set_status(uid, status):
    """approved / pending / inactive (never touches the admin account)."""
    execute("UPDATE users SET status=? WHERE id=? AND role!='admin'", (status, uid))

def search(role, term, uid_num):
    like = f'%{term}%'
    return query('SELECT * FROM users WHERE role=? AND (name LIKE ? OR id=? OR IFNULL(student_no,"") LIKE ?)',
                 (role, like, uid_num, like))
