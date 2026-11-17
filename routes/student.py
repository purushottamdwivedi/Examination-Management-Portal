"""Student: browse exams, book / cancel slots, history, results."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from models import exam as exam_model, slot as slot_model, booking as booking_model, result as result_model
from utils import role_required, today

bp = Blueprint('student', __name__, url_prefix='/student')

@bp.route('')
@role_required('student')
def dashboard():
    uid = session['uid']
    upcoming = [b for b in booking_model.for_student(uid) if b['status'] == 'Booked' and b['date'] >= today()]
    return render_template('student_dash.html', upcoming=upcoming,
                           results=result_model.published_for_student(uid),
                           open_exams=exam_model.count_open_for_booking(),
                           open_slots=slot_model.count_available_for_booking())

@bp.route('/exams')
@role_required('student')
def student_exams():
    t = request.args.get('q', '').strip()
    ty = request.args.get('type', '')
    st = request.args.get('status', 'Booking Open')
    exams = exam_model.for_student(t, ty, st)
    slots = {e['id']: slot_model.for_exam(e['id'], hide_cancelled=True) for e in exams}
    return render_template('student_exams.html', exams=exams, slots=slots, t=t, ty=ty, st=st,
                           booked=booking_model.booked_exam_ids(session['uid']))

@bp.route('/book/<int:sid>', methods=['POST'])
@role_required('student')
def book(sid):
    uid = session['uid']
    s = slot_model.get(sid) or abort(404)
    e = exam_model.get(s['exam_id'])
    slot_model.refresh(sid)
    s = slot_model.get(sid)
    if e['status'] != 'Booking Open' or not (e['bk_start'] <= today() <= e['bk_end']):
        flash('Booking is not open for this examination.', 'danger')
    elif booking_model.has_active(uid, e['id']):
        flash('You already have a booking for this examination.', 'warning')
    elif s['status'] != 'Available' or s['available'] < 1:
        flash('Slot is full or unavailable.', 'danger')
    else:
        booking_model.create(uid, sid, e['id'])
        slot_model.refresh(sid)          # closes the slot automatically when full
        flash('Slot booked!', 'success')
    return redirect(request.referrer or url_for('student.student_exams'))

@bp.route('/cancel/<int:bid>', methods=['POST'])
@role_required('student')
def cancel(bid):
    b = booking_model.get_for_student(bid, session['uid']) or abort(404)
    e = exam_model.get(b['exam_id'])
    if b['status'] != 'Booked' or today() > e['bk_end'] or e['status'] != 'Booking Open':
        flash('Booking can no longer be cancelled (deadline passed).', 'danger')
    else:
        booking_model.set_status(bid, 'Cancelled')
        slot_model.refresh(b['slot_id'])
        flash('Booking cancelled.', 'success')
    return redirect(url_for('student.student_history'))

@bp.route('/history')
@role_required('student')
def student_history():
    uid = session['uid']
    return render_template('student_history.html', rows=booking_model.for_student(uid),
                           fb=result_model.published_map(uid), exams=exam_model.all_map())
