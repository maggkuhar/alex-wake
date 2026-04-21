from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils import current_user
from депонирование.logic import get_my_paintings_with_deposit, create_deposit

bp = Blueprint('deposit_bp', __name__, template_folder='templates')


@bp.route('/deposit', methods=['GET', 'POST'])
def deposit():
    user = current_user()
    if not user or user['role'] != 'artist':
        return redirect(url_for('cabinet_bp.login'))

    my_paintings = get_my_paintings_with_deposit(user['id'])

    if request.method == 'POST':
        painting_id      = request.form.get('painting_id')
        artist_full_name = request.form.get('artist_full_name', '').strip()
        passport         = request.form.get('passport', '').strip()
        description      = request.form.get('description', '').strip()
        if painting_id and artist_full_name:
            create_deposit(painting_id, user['id'], artist_full_name, passport, description)
            flash('Заявка на депонирование отправлена. Мы свяжемся с вами.')
        return redirect(url_for('deposit_bp.deposit'))

    return render_template('deposit.html', my_paintings=my_paintings)
