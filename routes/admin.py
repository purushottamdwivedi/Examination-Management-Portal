"""Admin: courses, exams, rubrics, examiners, slots, bookings, search."""
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from models import user as user_model, course as course_model, exam as exam_model, rubric as rubric_model
from models import slot as slot_model, booking as booking_model
from config import EXAM_STATUS
from utils import role_required

bp = Blueprint('admin', __name__, url_prefix='/admin')

def back(default='admin.dashboard'):
    return redirect(request.referrer or url_for(default))

def exam_data(f):
    keys = ('course_id', 'name', 'type', 'max_marks', 'sc_start', 'sc_end', 'bk_start', 'bk_end', 'venue')
    d = {k: f.get(k) for k in keys}
    d['name'] = d['name'].strip()
    d['duration'] = f.get('duration') or 0
    return d

def dates_ok(d):
    return d['sc_start'] <= d['sc_end'] and d['bk_start'] <= d['bk_end']

# ---- dashboard ----
@bp.route('')
@role_required('admin')
def dashboard():
    stats = {'Courses': course_model.count(), 'Examinations': exam_model.count(),
             'Examiners': user_model.count('examiner'), 'Students': user_model.count('student'),
             'Slots': slot_model.count(), 'Bookings': booking_model.count()}
    return render_template('admin_dash.html', stats=stats, pending=user_model.pending_examiners(),
                           trend=exam_model.bookings_per_exam())

# ---- courses ----
@bp.route('/courses', methods=['GET', 'POST'])
@role_required('admin')
def admin_courses():
    if request.method == 'POST':
        f = request.form
        try:
            course_model.create(f['code'].strip(), f['name'].strip(), f['description'], f.get('credits'), f['status'])
            flash('Course created.', 'success')
        except sqlite3.IntegrityError:
            flash('Course code already exists.', 'danger')
        return redirect(url_for('admin.admin_courses'))
    return render_template('admin_courses.html', courses=course_model.all(), edit=None)

@bp.route('/courses/<int:cid>/edit', methods=['GET', 'POST'])
@role_required('admin')
def course_edit(cid):
    c = course_model.get(cid) or abort(404)
    if request.method == 'POST':
        f = request.form
        try:
            course_model.update(cid, f['code'], f['name'], f['description'], f.get('credits'), f['status'])
            flash('Course updated.', 'success')
            return redirect(url_for('admin.admin_courses'))
        except sqlite3.IntegrityError:
            flash('Course code already exists.', 'danger')
    return render_template('admin_courses.html', courses=course_model.all(), edit=c)

@bp.route('/courses/<int:cid>/delete', methods=['POST'])
@role_required('admin')
def course_delete(cid):
    if course_model.has_exams(cid):
        flash('Cannot delete: course has examinations. Mark it Inactive instead.', 'warning')
    else:
        course_model.delete(cid)
        flash('Course removed.', 'success')
    return redirect(url_for('admin.admin_courses'))

# ---- exams ----
@bp.route('/exams', methods=['GET', 'POST'])
@role_required('admin')
def admin_exams():
    if request.method == 'POST':
        d = exam_data(request.form)
        if not dates_ok(d):
            flash('End dates must not precede start dates.', 'danger')
        else:
            exam_model.create(d)
            flash('Examination created (Draft).', 'success')
        return redirect(url_for('admin.admin_exams'))
    return render_template('admin_exams.html', exams=exam_model.all(), courses=course_model.active(), edit=None)

@bp.route('/exams/<int:eid>/edit', methods=['GET', 'POST'])
@role_required('admin')
def exam_edit(eid):
    e = exam_model.get(eid) or abort(404)
    if request.method == 'POST':
        d = exam_data(request.form)
        if not dates_ok(d):
            flash('End dates must not precede start dates.', 'danger')
        else:
            exam_model.update(eid, d)
            flash('Examination updated.', 'success')
            return redirect(url_for('admin.admin_exams'))
    return render_template('admin_exams.html', exams=[], courses=course_model.all(), edit=e)

@bp.route('/exams/<int:eid>/delete', methods=['POST'])
@role_required('admin')
def exam_delete(eid):
    if exam_model.has_slots(eid):
        flash('Cannot delete: slots exist. Set status to Closed/Completed instead.', 'warning')
    else:
        exam_model.delete(eid)
        flash('Examination removed.', 'success')
    return redirect(url_for('admin.admin_exams'))

@bp.route('/exams/<int:eid>/status', methods=['POST'])
@role_required('admin')
def exam_status(eid):
    s = request.form['status']
    if s not in EXAM_STATUS:
        abort(400)
    exam_model.set_status(eid, s)
    flash(f'Status set to {s}.', 'success')
    return back('admin.admin_exams')

@bp.route('/exams/<int:eid>/publish', methods=['POST'])
@role_required('admin')
def exam_publish(eid):
    v = 1 if request.form.get('v') == '1' else 0
    exam_model.set_published(eid, v)
    flash('Results ' + ('published.' if v else 'unpublished.'), 'success')
    return back('admin.admin_exams')

@bp.route('/exams/<int:eid>')
@role_required('admin')
def exam_detail(eid):
    e = exam_model.get(eid) or abort(404)
    rubrics = rubric_model.for_exam(eid)
    return render_template('admin_exam_detail.html', e=e, rubrics=rubrics,
                           assigned=exam_model.assigned_examiners(eid),
                           available=exam_model.unassigned_examiners(eid),
                           slots=slot_model.for_exam(eid),
                           total_w=sum(r['weight'] for r in rubrics))

@bp.route('/exams/<int:eid>/examiners', methods=['POST'])
@role_required('admin')
def exam_assign(eid):
    if request.form.get('remove'):
        exam_model.unassign(eid, request.form['remove'])
    else:
        exam_model.assign(eid, request.form['examiner_id'])
    return redirect(url_for('admin.exam_detail', eid=eid))

# ---- rubrics ----
@bp.route('/exams/<int:eid>/rubrics', methods=['POST'])
@role_required('admin')
def rubric_add(eid):
    f = request.form
    if float(f['max_marks']) <= 0 or float(f['weight']) <= 0:
        flash('Marks and weightage must be positive.', 'danger')
    else:
        rubric_model.create(eid, f['name'], f['max_marks'], f['weight'], f['description'])
        flash('Rubric added.', 'success')
    return redirect(url_for('admin.exam_detail', eid=eid))

@bp.route('/rubrics/<int:rid>/<act>', methods=['POST'])
@role_required('admin')
def rubric_act(rid, act):
    r = rubric_model.get(rid) or abort(404)
    if act == 'delete':
        if rubric_model.in_use(rid):
            flash('Rubric already used in evaluations.', 'warning')
        else:
            rubric_model.delete(rid)
            flash('Rubric removed.', 'success')
    elif act == 'edit':
        f = request.form
        rubric_model.update(rid, f['name'], f['max_marks'], f['weight'], f['description'])
        flash('Rubric updated.', 'success')
    return redirect(url_for('admin.exam_detail', eid=r['exam_id']))

# ---- examiners / students ----
@bp.route('/users/<role>')
@role_required('admin')
def admin_users(role):
    if role not in ('student', 'examiner'):
        abort(404)
    return render_template('admin_users.html', role=role, rows=user_model.list_by_role(role))

@bp.route('/users/<int:uid>/status', methods=['POST'])
@role_required('admin')
def user_status(uid):
    s = request.form['status']
    u = user_model.get(uid)
    if s not in ('approved', 'inactive', 'pending') or not u or u['role'] == 'admin':
        abort(400)
    user_model.set_status(uid, s)
    flash(f"{u['name']} set to {s}.", 'success')
    return back()

# ---- slots & bookings ----
@bp.route('/slots')
@role_required('admin')
def admin_slots():
    return render_template('admin_slots.html', slots=slot_model.all())

@bp.route('/slots/<int:sid>/examiner', methods=['GET', 'POST'])
@role_required('admin')
def slot_examiner(sid):
    s = slot_model.get_full(sid) or abort(404)
    examiners = exam_model.assigned_examiners(s['exam_id'], approved_only=True)
    if request.method == 'POST':
        if int(request.form['examiner_id']) not in [x['id'] for x in examiners]:
            abort(400)
        slot_model.set_examiner(sid, request.form['examiner_id'])
        flash('Examiner reassigned.', 'success')
        return redirect(url_for('admin.admin_slots'))
    return render_template('admin_reassign.html', s=s, examiners=examiners)

@bp.route('/bookings')
@role_required('admin')
def admin_bookings():
    return render_template('admin_bookings.html', rows=booking_model.all())

@bp.route('/bookings/<int:bid>/reschedule', methods=['GET', 'POST'])
@role_required('admin')
def reschedule(bid):
    b = booking_model.get(bid) or abort(404)
    if b['status'] != 'Booked':
        flash('Only active bookings can be rescheduled.', 'warning')
        return redirect(url_for('admin.admin_bookings'))
    options = slot_model.reschedule_options(b['exam_id'], b['slot_id'])
    if request.method == 'POST':
        new = next((s for s in options if str(s['id']) == request.form.get('slot_id')), None)
        if not new:
            flash('Selected slot is unavailable.', 'danger')
        else:
            old = b['slot_id']
            booking_model.move(bid, new['id'])
            slot_model.refresh(old)
            slot_model.refresh(new['id'])
            flash('Booking rescheduled.', 'success')
            return redirect(url_for('admin.admin_bookings'))
    return render_template('admin_reschedule.html', b=b, slots=options)

# ---- search ----
@bp.route('/search')
@role_required('admin')
def admin_search():
    t = request.args.get('q', '').strip()
    n = int(t) if t.isdigit() else -1
    return render_template('admin_search.html', t=t,
        students=user_model.search('student', t, n) if t else [],
        examiners=user_model.search('examiner', t, n) if t else [],
        exams=exam_model.search(t, n) if t else [],
        bookings=booking_model.search(t, n) if t else [])
