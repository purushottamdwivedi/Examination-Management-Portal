"""slots table: examination slots created by examiners."""
from database import query, execute

BASE = """SELECT s.*, e.name exam, e.status estatus, c.code, u.name examiner FROM slots s
  JOIN exams e ON e.id=s.exam_id JOIN courses c ON c.id=e.course_id JOIN users u ON u.id=s.examiner_id"""

def create(exam_id, examiner_id, date, start, end, capacity, location):
    return execute('INSERT INTO slots(exam_id,examiner_id,date,start,end,capacity,available,location) VALUES(?,?,?,?,?,?,?,?)',
                   (exam_id, examiner_id, date, start, end, capacity, capacity, location))

def get(sid):
    return query('SELECT * FROM slots WHERE id=?', (sid,), True)

def get_full(sid):
    return query(BASE + ' WHERE s.id=?', (sid,), True)

def get_owned(sid, examiner_id):
    return query('SELECT * FROM slots WHERE id=? AND examiner_id=?', (sid, examiner_id), True)

def all():
    return query(BASE + ' ORDER BY s.date, s.start')

def for_exam(eid, hide_cancelled=False):
    return query(BASE + ' WHERE s.exam_id=?' + (" AND s.status!='Cancelled'" if hide_cancelled else '') +
                 ' ORDER BY s.date, s.start', (eid,))

def for_examiner(uid):
    return query(BASE + ' WHERE s.examiner_id=? ORDER BY s.date, s.start', (uid,))

def reschedule_options(exam_id, exclude_slot):
    return query(BASE + " WHERE s.exam_id=? AND s.id!=? AND s.status='Available' AND s.available>0", (exam_id, exclude_slot))

def update(sid, date, start, end, capacity, location):
    execute("UPDATE slots SET date=?,start=?,end=?,capacity=?,available=?,location=?,status='Available' WHERE id=?",
            (date, start, end, capacity, capacity, location, sid))

def delete(sid):
    execute('DELETE FROM slots WHERE id=?', (sid,))

def set_examiner(sid, examiner_id):
    execute('UPDATE slots SET examiner_id=? WHERE id=?', (examiner_id, sid))

def overlaps(examiner_id, date, start, end, ignore_id=-1):
    return bool(query("""SELECT 1 FROM slots WHERE examiner_id=? AND date=? AND start<? AND end>?
                         AND status!='Cancelled' AND id!=?""", (examiner_id, date, end, start, ignore_id)))

def has_bookings(sid, active_only=False):
    sql = 'SELECT 1 FROM bookings WHERE slot_id=?' + (" AND status='Booked'" if active_only else '')
    return bool(query(sql, (sid,)))

def refresh(sid):
    """Recalculate available seats from bookings; auto-close (Full) when capacity is reached."""
    s = get(sid)
    if not s or s['status'] in ('Cancelled', 'Completed'):
        return
    n = query("SELECT COUNT(*) c FROM bookings WHERE slot_id=? AND status IN ('Booked','Completed')", (sid,), True)['c']
    avail = max(s['capacity'] - n, 0)
    execute('UPDATE slots SET available=?, status=? WHERE id=?', (avail, 'Full' if avail == 0 else 'Available', sid))

def count():
    return query('SELECT COUNT(*) c FROM slots', one=True)['c']

def count_available_for_booking():
    return query("""SELECT COUNT(*) c FROM slots s JOIN exams e ON e.id=s.exam_id
                    WHERE e.status='Booking Open' AND s.status='Available'""", one=True)['c']
