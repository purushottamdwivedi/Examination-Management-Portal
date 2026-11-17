"""bookings table: a student booking a slot."""
from database import query, execute

def rows(where='1', args=()):
    """Bookings joined with student / exam / slot / examiner info (and total marks if evaluated)."""
    return query(f"""SELECT b.*, u.name student, u.student_no, e.name exam, c.code, s.date, s.start, s.end, x.name examiner,
      (SELECT total FROM results r WHERE r.booking_id=b.id) total
      FROM bookings b JOIN users u ON u.id=b.student_id JOIN slots s ON s.id=b.slot_id
      JOIN exams e ON e.id=b.exam_id JOIN courses c ON c.id=e.course_id JOIN users x ON x.id=s.examiner_id
      WHERE {where} ORDER BY b.id DESC""", args)

def get(bid):
    r = rows('b.id=?', (bid,))
    return r[0] if r else None

def get_for_student(bid, student_id):
    return query('SELECT * FROM bookings WHERE id=? AND student_id=?', (bid, student_id), True)

def create(student_id, slot_id, exam_id):
    return execute('INSERT INTO bookings(student_id,slot_id,exam_id) VALUES(?,?,?)', (student_id, slot_id, exam_id))

def set_status(bid, status):
    execute('UPDATE bookings SET status=? WHERE id=?', (status, bid))

def move(bid, new_slot_id):
    execute('UPDATE bookings SET slot_id=? WHERE id=?', (new_slot_id, bid))

def has_active(student_id, exam_id):
    """Used to prevent duplicate bookings for the same examination."""
    return bool(query("SELECT 1 FROM bookings WHERE student_id=? AND exam_id=? AND status IN ('Booked','Completed')",
                      (student_id, exam_id)))

def booked_exam_ids(student_id):
    return {r['exam_id'] for r in query("SELECT exam_id FROM bookings WHERE student_id=? AND status IN ('Booked','Completed')", (student_id,))}

def all():
    return rows()

def for_student(uid):
    return rows('b.student_id=?', (uid,))

def for_slot(sid):
    return rows('b.slot_id=?', (sid,))

def for_examiner_booking(bid, examiner_id):
    """Booking only if it belongs to one of this examiner's own slots."""
    r = rows('b.id=? AND x.id=?', (bid, examiner_id))
    return r[0] if r else None

def pending_for_examiner(examiner_id):
    return rows("x.id=? AND b.status='Booked' AND b.id NOT IN (SELECT booking_id FROM results)", (examiner_id,))

def search(term, id_num):
    return rows('(u.name LIKE ? OR b.id=? OR e.name LIKE ?)', (f'%{term}%', id_num, f'%{term}%'))

def count():
    return query('SELECT COUNT(*) c FROM bookings', one=True)['c']

def count_for_examiner(examiner_id):
    return query("""SELECT COUNT(*) c FROM bookings b JOIN slots s ON s.id=b.slot_id
                    WHERE s.examiner_id=? AND b.status IN ('Booked','Completed')""", (examiner_id,), True)['c']
