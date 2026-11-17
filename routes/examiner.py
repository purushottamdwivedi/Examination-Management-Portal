"""Examiner: slots, booked students, evaluation."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from models import exam as exam_model, rubric as rubric_model, slot as slot_model
from models import booking as booking_model, result as result_model
from utils import role_required, today

bp = Blueprint('examiner', __name__, url_prefix='/examiner')

def my_exam(eid):
    return exam_model.get_if_assigned(eid, session['uid']) or abort(403)

def my_slot(sid):
    return slot_model.get_owned(sid, session['uid']) or abort(403)

def slot_error(e, f, sid=-1):
    """Backend validation for creating/updating a slot. Returns an error string or None."""
    if e['status'] != 'Slot Creation':
        return 'Slot creation is not open for this examination.'
    if not (e['sc_start'] <= today() <= e['sc_end']):
        return 'Today is outside the slot creation period.'
    if not (f['date'] and f['start'] < f['end']):
        return 'End time must be after start time.'
    if int(f['capacity']) < 1:
        return 'Capacity must be at least 1.'
    if f['date'] < today():
        return 'Slot date cannot be in the past.'
    if slot_model.overlaps(session['uid'], f['date'], f['start'], f['end'], sid):
        return 'You already have an overlapping slot.'
    return None

@bp.route('')
@role_required('examiner')
def dashboard():
    uid = session['uid']
    return render_template('examiner_dash.html', exams=exam_model.for_examiner(uid),
                           slots=slot_model.for_examiner(uid), booked=booking_model.count_for_examiner(uid),
                           pending=booking_model.pending_for_examiner(uid))

@bp.route('/slots/new/<int:eid>', methods=['GET', 'POST'])
@role_required('examiner')
def slot_new(eid):
    e = my_exam(eid)
    if request.method == 'POST':
        f = request.form
        err = slot_error(e, f)
        if err:
            flash(err, 'danger')
        else:
            slot_model.create(eid, session['uid'], f['date'], f['start'], f['end'], f['capacity'], f.get('location'))
            flash('Slot created.', 'success')
            return redirect(url_for('examiner.dashboard'))
    return render_template('slot_form.html', e=e, s=None)

@bp.route('/slots/<int:sid>/edit', methods=['GET', 'POST'])
@role_required('examiner')
def slot_edit(sid):
    s = my_slot(sid)
    e = my_exam(s['exam_id'])
    if slot_model.has_bookings(sid, active_only=True):
        flash('Slot already has bookings.', 'warning')
        return redirect(url_for('examiner.dashboard'))
    if request.method == 'POST':
        f = request.form
        err = slot_error(e, f, sid)
        if err:
            flash(err, 'danger')
        else:
            slot_model.update(sid, f['date'], f['start'], f['end'], f['capacity'], f.get('location'))
            flash('Slot updated.', 'success')
            return redirect(url_for('examiner.dashboard'))
    return render_template('slot_form.html', e=e, s=s)

@bp.route('/slots/<int:sid>/delete', methods=['POST'])
@role_required('examiner')
def slot_delete(sid):
    s = my_slot(sid)
    e = my_exam(s['exam_id'])
    if e['status'] in ('Booking Open', 'Closed', 'Completed') or slot_model.has_bookings(sid):
        flash('Cannot remove: booking has started or bookings exist.', 'warning')
    else:
        slot_model.delete(sid)
        flash('Slot removed.', 'success')
    return redirect(url_for('examiner.dashboard'))

@bp.route('/slots/<int:sid>')
@role_required('examiner')
def slot_students(sid):
    s = my_slot(sid)
    return render_template('slot_students.html', s=s, rows=booking_model.for_slot(sid))

def calc_total(rubrics, marks, max_marks):
    """Weighted score scaled to the exam's maximum marks."""
    weighted = sum(marks[r['id']] / r['max_marks'] * r['weight'] for r in rubrics)
    return weighted / sum(r['weight'] for r in rubrics) * max_marks

def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return -1

@bp.route('/evaluate/<int:bid>', methods=['GET', 'POST'])
@role_required('examiner')
def evaluate(bid):
    b = booking_model.for_examiner_booking(bid, session['uid'])
    if not b:
        abort(403)          # examiners can only evaluate students in their own slots
    if b['status'] == 'Cancelled':
        abort(400)
    e = exam_model.get(b['exam_id'])
    rubrics = rubric_model.for_exam(e['id'])
    if request.method == 'POST':
        ok, marks, total = True, {}, 0
        if rubrics:
            for r in rubrics:
                m = to_float(request.form.get(f'm{r["id"]}'))
                if not 0 <= m <= r['max_marks']:
                    ok = False
                    flash(f'"{r["name"]}" must be between 0 and {r["max_marks"]}.', 'danger')
                marks[r['id']] = m
            if ok:
                total = calc_total(rubrics, marks, e['max_marks'])
        else:
            total = to_float(request.form.get('total'))
            if not 0 <= total <= e['max_marks']:
                ok = False
                flash(f'Marks must be between 0 and {e["max_marks"]}.', 'danger')
        if ok:
            result_model.save(bid, marks, total, request.form['remarks'])
            booking_model.set_status(bid, 'Completed')
            flash('Marks and remarks submitted.', 'success')
            return redirect(url_for('examiner.slot_students', sid=b['slot_id']))
    return render_template('evaluate.html', b=b, e=e, rubrics=rubrics,
                           old=result_model.rubric_marks(bid), res=result_model.get(bid))
