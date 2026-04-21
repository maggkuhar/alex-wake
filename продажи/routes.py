from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from utils import current_user
from продажи.logic import get_cart_paintings, get_dialogs, get_dialog_messages

bp = Blueprint('sales', __name__, template_folder='templates')


@bp.route('/cart')
def cart():
    cart = session.get('cart', {})
    paintings, total = get_cart_paintings(cart)
    return render_template('cart.html', paintings=paintings, total=total, active_page='cart')


@bp.route('/cart/add', methods=['POST'])
def cart_add():
    pid = str(request.form.get('painting_id'))
    qty = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    cart[pid] = cart.get(pid, 0) + qty
    session['cart'] = cart
    return jsonify({'ok': True, 'count': sum(cart.values())})


@bp.route('/cart/remove', methods=['POST'])
def cart_remove():
    pid = str(request.form.get('painting_id'))
    cart = session.get('cart', {})
    cart.pop(pid, None)
    session['cart'] = cart
    return jsonify({'ok': True, 'count': sum(cart.values())})


@bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if not current_user():
        return redirect(url_for('cabinet_bp.login'))
    if request.method == 'POST':
        # TODO: создать заказ + подключить оплату
        session['cart'] = {}
        flash('Заказ оформлен! Мы свяжемся с вами.')
        return redirect(url_for('cabinet_bp.cabinet'))
    cart = session.get('cart', {})
    paintings, total = get_cart_paintings(cart)
    return render_template('checkout.html', paintings=paintings, total=total)


@bp.route('/messages')
def messages():
    user = current_user()
    if not user:
        return redirect(url_for('cabinet_bp.login'))
    dialogs = get_dialogs(user['id'])
    return render_template('messages.html', dialogs=dialogs, active_page='messages')


@bp.route('/messages/<int:to_id>', methods=['GET', 'POST'])
def dialog(to_id):
    user = current_user()
    if not user:
        return redirect(url_for('cabinet_bp.login'))
    content = None
    painting_id = None
    if request.method == 'POST':
        content = request.form.get('content', '').strip() or None
        painting_id = request.form.get('painting_id') or None
    msgs, interlocutor = get_dialog_messages(user['id'], to_id, content, painting_id)
    return render_template('dialog.html', messages=msgs, interlocutor=interlocutor)
