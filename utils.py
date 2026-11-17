"""Shared helpers: current user, role-based access control, dates."""
from datetime import date
from functools import wraps
from flask import session, redirect, url_for, abort, render_template
from models import user as user_model

def today():
    return date.today().isoformat()

def current_user():
    return user_model.get(session['uid']) if 'uid' in session else None

def home_url(u):
    return url_for(f"{u['role']}.dashboard")

def role_required(role):
    """Allow only logged-in users with the given role (examiners must also be approved)."""
    def deco(f):
        @wraps(f)
        def wrapper(*a, **k):
            u = current_user()
            if not u:
                return redirect(url_for('auth.login'))
            if u['role'] != role:
                abort(403)
            if role == 'examiner' and u['status'] != 'approved':
                return render_template('pending.html')
            return f(*a, **k)
        return wrapper
    return deco
