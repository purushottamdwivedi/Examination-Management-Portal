"""Login, registration, logout, profile (shared by all roles)."""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from models import user as user_model
from utils import current_user, home_url

bp = Blueprint('auth', __name__)

@bp.route('/')
def index():
    u = current_user()
    return redirect(home_url(u) if u else url_for('auth.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = user_model.get_by_email(request.form['email'].strip().lower())
        if u and check_password_hash(u['password'], request.form['password']):
            if u['status'] == 'inactive':
                flash('Your account is deactivated. Contact admin.', 'danger')
            else:
                session['uid'] = u['id']
                return redirect(home_url(u))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        f = request.form
        role = f.get('role')
        if role not in ('student', 'examiner'):
            abort(400)
        email = f['email'].strip().lower()
        if len(f['password']) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        elif user_model.get_by_email(email):
            flash('Email already registered.', 'danger')
        else:
            user_model.create(role, f['name'].strip(), email, generate_password_hash(f['password']),
                              f.get('phone'), f.get('department'), f.get('student_no'),
                              'pending' if role == 'examiner' else 'approved')
            flash('Registered! ' + ('Await admin approval, then log in.' if role == 'examiner' else 'Please log in.'), 'success')
            return redirect(url_for('auth.login'))
    return render_template('register.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@bp.route('/profile', methods=['GET', 'POST'])
def profile():
    u = current_user()
    if not u:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        f = request.form
        user_model.update_profile(u['id'], f['name'], f.get('phone'), f.get('department'), f.get('student_no'))
        if f.get('password'):
            if len(f['password']) < 6:
                flash('Password too short.', 'danger')
                return redirect(url_for('auth.profile'))
            user_model.update_password(u['id'], generate_password_hash(f['password']))
        flash('Profile updated.', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('profile.html')
