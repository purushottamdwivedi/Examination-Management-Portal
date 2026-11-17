"""evaluations (marks per rubric) and results (final total + remarks)."""
from database import query, execute

def rubric_marks(bid):
    return {r['rubric_id']: r['marks'] for r in query('SELECT * FROM evaluations WHERE booking_id=?', (bid,))}

def get(bid):
    return query('SELECT * FROM results WHERE booking_id=?', (bid,), True)

def save(bid, rubric_marks, total, remarks):
    """Store per-rubric marks, the final total and remarks (insert or overwrite)."""
    for rid, m in rubric_marks.items():
        execute('INSERT OR REPLACE INTO evaluations VALUES(?,?,?)', (bid, rid, m))
    execute('INSERT OR REPLACE INTO results(booking_id,total,remarks) VALUES(?,?,?)', (bid, round(total, 2), remarks))

def published_for_student(uid):
    return query("""SELECT r.*, e.name exam, b.id bid FROM results r JOIN bookings b ON b.id=r.booking_id
                    JOIN exams e ON e.id=b.exam_id WHERE b.student_id=? AND e.published=1""", (uid,))

def published_map(uid):
    return {r['booking_id']: r for r in published_for_student(uid)}
