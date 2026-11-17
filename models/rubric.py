"""rubrics table: evaluation criteria for an exam."""
from database import query, execute

def create(exam_id, name, max_marks, weight, description):
    return execute('INSERT INTO rubrics(exam_id,name,max_marks,weight,description) VALUES(?,?,?,?,?)',
                   (exam_id, name, max_marks, weight, description))

def get(rid):
    return query('SELECT * FROM rubrics WHERE id=?', (rid,), True)

def for_exam(eid):
    return query('SELECT * FROM rubrics WHERE exam_id=?', (eid,))

def update(rid, name, max_marks, weight, description):
    execute('UPDATE rubrics SET name=?, max_marks=?, weight=?, description=? WHERE id=?',
            (name, max_marks, weight, description, rid))

def in_use(rid):
    return bool(query('SELECT 1 FROM evaluations WHERE rubric_id=?', (rid,)))

def delete(rid):
    execute('DELETE FROM rubrics WHERE id=?', (rid,))
