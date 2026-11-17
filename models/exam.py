"""exams table + the exam <-> examiner assignment table (exam_examiners)."""
from database import query, execute

COLS = ('course_id', 'name', 'type', 'duration', 'max_marks', 'sc_start', 'sc_end', 'bk_start', 'bk_end', 'venue')
JOIN = 'SELECT e.*, c.code, c.name cname FROM exams e JOIN courses c ON c.id=e.course_id'

def create(d):
    return execute(f"INSERT INTO exams({','.join(COLS)}) VALUES({','.join('?' * len(COLS))})", [d[c] for c in COLS])

def update(eid, d):
    execute(f"UPDATE exams SET {','.join(c + '=?' for c in COLS)} WHERE id=?", [d[c] for c in COLS] + [eid])

def get(eid):
    return query(JOIN + ' WHERE e.id=?', (eid,), True)

def all():
    return query(JOIN + ' ORDER BY e.id DESC')

def all_map():
    return {e['id']: e for e in all()}

def has_slots(eid):
    return bool(query('SELECT 1 FROM slots WHERE exam_id=?', (eid,)))

def delete(eid):
    execute('DELETE FROM rubrics WHERE exam_id=?', (eid,))
    execute('DELETE FROM exam_examiners WHERE exam_id=?', (eid,))
    execute('DELETE FROM exams WHERE id=?', (eid,))

def set_status(eid, status):
    execute('UPDATE exams SET status=? WHERE id=?', (status, eid))

def set_published(eid, flag):
    execute('UPDATE exams SET published=? WHERE id=?', (flag, eid))

def count():
    return query('SELECT COUNT(*) c FROM exams', one=True)['c']

def count_open_for_booking():
    return query("SELECT COUNT(*) c FROM exams WHERE status='Booking Open'", one=True)['c']

def search(term, id_num):
    return query(JOIN + ' WHERE e.name LIKE ? OR e.id=?', (f'%{term}%', id_num))

def bookings_per_exam():
    return query("""SELECT e.name, COUNT(b.id) n FROM exams e
                    LEFT JOIN bookings b ON b.exam_id=e.id AND b.status!='Cancelled' GROUP BY e.id""")

def for_student(text='', exam_type='', status=''):
    sql, a = JOIN + " WHERE e.status!='Draft'", []
    if text:
        sql += ' AND (e.name LIKE ? OR c.name LIKE ? OR c.code LIKE ?)'; a += [f'%{text}%'] * 3
    if exam_type:
        sql += ' AND e.type=?'; a.append(exam_type)
    if status:
        sql += ' AND e.status=?'; a.append(status)
    return query(sql, a)

# --- examiner assignment ---
def assign(eid, examiner_id):
    execute('INSERT OR IGNORE INTO exam_examiners VALUES(?,?)', (eid, examiner_id))

def unassign(eid, examiner_id):
    execute('DELETE FROM exam_examiners WHERE exam_id=? AND examiner_id=?', (eid, examiner_id))

def assigned_examiners(eid, approved_only=False):
    sql = 'SELECT u.* FROM users u JOIN exam_examiners x ON x.examiner_id=u.id WHERE x.exam_id=?'
    return query(sql + (" AND u.status='approved'" if approved_only else ''), (eid,))

def unassigned_examiners(eid):
    return query("""SELECT * FROM users WHERE role='examiner' AND status='approved'
                    AND id NOT IN (SELECT examiner_id FROM exam_examiners WHERE exam_id=?)""", (eid,))

def for_examiner(uid):
    return query(JOIN + ' JOIN exam_examiners x ON x.exam_id=e.id WHERE x.examiner_id=?', (uid,))

def get_if_assigned(eid, uid):
    return query(JOIN + ' JOIN exam_examiners x ON x.exam_id=e.id WHERE e.id=? AND x.examiner_id=?', (eid, uid), True)
