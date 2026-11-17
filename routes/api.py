"""Read-only JSON API (login required)."""
from flask import Blueprint, jsonify, abort
from models import exam as exam_model, slot as slot_model, booking as booking_model
from utils import current_user

bp = Blueprint('api', __name__, url_prefix='/api')

def need_login():
    return current_user() or abort(401)

@bp.route('/exams')
def api_exams():
    need_login()
    return jsonify([dict(r) for r in exam_model.all()])

@bp.route('/slots')
def api_slots():
    need_login()
    return jsonify([dict(r) for r in slot_model.all()])

@bp.route('/bookings')
def api_bookings():
    u = need_login()
    if u['role'] == 'admin':
        rows = booking_model.all()
    elif u['role'] == 'student':
        rows = booking_model.for_student(u['id'])
    else:
        rows = booking_model.rows('x.id=?', (u['id'],))
    return jsonify([dict(r) for r in rows])
