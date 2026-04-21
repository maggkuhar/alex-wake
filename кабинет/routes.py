from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils import current_user
from кабинет.logic import register_user, authenticate_user, get_cabinet_data

bp = Blueprint('cabinet_bp', __name__, template_folder='templates')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role     = request.form.get('role', 'buyer')
        if not name or not email or not password:
            flash('Заполните все поля')
            return render_template('register.html')
        user, error = register_user(name, email, password, role)
        if error:
            flash(error)
            return render_template('register.html')
        session['user_id'] = user['id']
        return redirect(url_for('cabinet_bp.cabinet'))
    return render_template('register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = authenticate_user(email, password)
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('cabinet_bp.cabinet'))
        flash('Неверный email или пароль')
    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('gallery.index'))


@bp.route('/cabinet')
def cabinet():
    user = current_user()
    if not user:
        return redirect(url_for('cabinet_bp.login'))
    orders, favorites, my_paintings, deposited_ids = get_cabinet_data(user['id'], user['role'])
    return render_template('cabinet.html', orders=orders, favorites=favorites,
        my_paintings=my_paintings, deposited_ids=deposited_ids, active_page='cabinet')
