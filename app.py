from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from database import init_db, get_db
import hashlib, os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'alexwake-secret-key')

# ─── Утилиты ────────────────────────────────────────────────────────────────

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def current_user():
    if 'user_id' not in session:
        return None
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    db.close()
    return user

@app.context_processor
def inject_globals():
    user = current_user()
    cart = session.get('cart', {})
    cart_count = sum(cart.values())
    return dict(user=user, cart_count=cart_count)

# ─── Блок 1: Витрина + каталог ──────────────────────────────────────────────

@app.route('/')
def index():
    db = get_db()
    featured = db.execute('''SELECT p.*, u.name as artist_name FROM paintings p
        LEFT JOIN users u ON p.artist_id = u.id
        WHERE p.in_stock=1 ORDER BY p.rating DESC, p.views DESC LIMIT 8''').fetchall()
    artists = db.execute('''SELECT * FROM users WHERE role="artist"
        ORDER BY rating DESC LIMIT 6''').fetchall()
    db.close()
    return render_template('index.html', featured=featured, artists=artists, active_page='catalog')

@app.route('/catalog')
def catalog():
    db = get_db()
    themes = db.execute('SELECT * FROM themes ORDER BY name').fetchall()
    techniques = db.execute('SELECT * FROM techniques ORDER BY name').fetchall()

    theme_id   = request.args.get('theme', '')
    technique_id = request.args.get('technique', '')
    price_min  = request.args.get('price_min', '')
    price_max  = request.args.get('price_max', '')
    sort       = request.args.get('sort', 'new')

    query = '''SELECT p.*, u.name as artist_name, t.name as theme_name
        FROM paintings p
        LEFT JOIN users u ON p.artist_id = u.id
        LEFT JOIN themes t ON p.theme_id = t.id
        WHERE p.in_stock=1'''
    params = []

    if theme_id:
        query += ' AND p.theme_id=?'; params.append(theme_id)
    if technique_id:
        query += ' AND p.technique_id=?'; params.append(technique_id)
    if price_min:
        query += ' AND p.price>=?'; params.append(price_min)
    if price_max:
        query += ' AND p.price<=?'; params.append(price_max)

    sorts = {'new': 'p.created_at DESC', 'price_asc': 'p.price ASC',
             'price_desc': 'p.price DESC', 'rating': 'p.rating DESC', 'popular': 'p.views DESC'}
    query += f' ORDER BY {sorts.get(sort, "p.created_at DESC")}'

    paintings = db.execute(query, params).fetchall()
    db.close()
    return render_template('catalog.html', paintings=paintings, themes=themes,
        techniques=techniques, active_page='catalog',
        filters=dict(theme=theme_id, technique=technique_id,
                     price_min=price_min, price_max=price_max, sort=sort))

@app.route('/painting/<int:pid>')
def painting(pid):
    db = get_db()
    db.execute('UPDATE paintings SET views=views+1 WHERE id=?', (pid,))
    db.commit()
    p = db.execute('''SELECT p.*, u.name as artist_name, u.avatar as artist_avatar,
        u.bio as artist_bio, u.rating as artist_rating,
        t.name as theme_name, tc.name as technique_name
        FROM paintings p
        LEFT JOIN users u ON p.artist_id = u.id
        LEFT JOIN themes t ON p.theme_id = t.id
        LEFT JOIN techniques tc ON p.technique_id = tc.id
        WHERE p.id=?''', (pid,)).fetchone()
    reviews = db.execute('''SELECT r.*, u.name as user_name FROM reviews r
        LEFT JOIN users u ON r.user_id=u.id
        WHERE r.painting_id=? ORDER BY r.created_at DESC''', (pid,)).fetchall()
    related = db.execute('''SELECT p.*, u.name as artist_name FROM paintings p
        LEFT JOIN users u ON p.artist_id=u.id
        WHERE p.theme_id=? AND p.id!=? AND p.in_stock=1 LIMIT 4''',
        (p['theme_id'], pid)).fetchall()
    is_favorite = False
    if 'user_id' in session:
        fav = db.execute('SELECT id FROM favorites WHERE user_id=? AND painting_id=?',
            (session['user_id'], pid)).fetchone()
        is_favorite = fav is not None
    db.close()
    if not p:
        return redirect(url_for('catalog'))
    return render_template('painting.html', p=p, reviews=reviews,
        related=related, is_favorite=is_favorite, active_page='catalog')

# ─── Блок 2: Корзина + заказ ────────────────────────────────────────────────

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    paintings = []
    total = 0
    if cart:
        db = get_db()
        for pid, qty in cart.items():
            p = db.execute('SELECT * FROM paintings WHERE id=?', (pid,)).fetchone()
            if p:
                paintings.append({'painting': p, 'qty': qty, 'subtotal': p['price'] * qty})
                total += p['price'] * qty
        db.close()
    return render_template('cart.html', paintings=paintings, total=total, active_page='cart')

@app.route('/cart/add', methods=['POST'])
def cart_add():
    pid = str(request.form.get('painting_id'))
    qty = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    cart[pid] = cart.get(pid, 0) + qty
    session['cart'] = cart
    return jsonify({'ok': True, 'count': sum(cart.values())})

@app.route('/cart/remove', methods=['POST'])
def cart_remove():
    pid = str(request.form.get('painting_id'))
    cart = session.get('cart', {})
    cart.pop(pid, None)
    session['cart'] = cart
    return jsonify({'ok': True, 'count': sum(cart.values())})

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if not current_user():
        return redirect(url_for('login'))
    if request.method == 'POST':
        # TODO: создать заказ + подключить оплату
        session['cart'] = {}
        flash('Заказ оформлен! Мы свяжемся с вами.')
        return redirect(url_for('cabinet'))
    cart = session.get('cart', {})
    paintings = []
    total = 0
    if cart:
        db = get_db()
        for pid, qty in cart.items():
            p = db.execute('SELECT * FROM paintings WHERE id=?', (pid,)).fetchone()
            if p:
                paintings.append({'painting': p, 'qty': qty, 'subtotal': p['price'] * qty})
                total += p['price'] * qty
        db.close()
    return render_template('checkout.html', paintings=paintings, total=total)

# ─── Блок 4: Профили художников ─────────────────────────────────────────────

@app.route('/artists')
def artists():
    db = get_db()
    artists = db.execute('''SELECT u.*,
        COUNT(p.id) as paintings_count FROM users u
        LEFT JOIN paintings p ON p.artist_id=u.id
        WHERE u.role="artist" GROUP BY u.id
        ORDER BY u.rating DESC''').fetchall()
    db.close()
    return render_template('artists.html', artists=artists, active_page='artists')

@app.route('/artist/<int:uid>')
def artist(uid):
    db = get_db()
    a = db.execute('SELECT * FROM users WHERE id=? AND role="artist"', (uid,)).fetchone()
    paintings = db.execute('''SELECT * FROM paintings WHERE artist_id=?
        ORDER BY created_at DESC''', (uid,)).fetchall()
    reviews = db.execute('''SELECT r.*, u.name as user_name FROM reviews r
        LEFT JOIN users u ON r.user_id=u.id
        WHERE r.artist_id=? ORDER BY r.created_at DESC''', (uid,)).fetchall()
    db.close()
    if not a:
        return redirect(url_for('artists'))
    return render_template('artist.html', a=a, paintings=paintings, reviews=reviews)

# ─── Блок 5: Чат ────────────────────────────────────────────────────────────

@app.route('/messages')
def messages():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    dialogs = db.execute('''SELECT u.id, u.name, u.avatar, u.role,
        (SELECT content FROM messages
         WHERE (from_user_id=u.id AND to_user_id=?) OR (from_user_id=? AND to_user_id=u.id)
         ORDER BY created_at DESC LIMIT 1) as last_msg,
        (SELECT COUNT(*) FROM messages WHERE from_user_id=u.id AND to_user_id=? AND is_read=0) as unread
        FROM users u WHERE u.id IN (
            SELECT DISTINCT CASE WHEN from_user_id=? THEN to_user_id ELSE from_user_id END
            FROM messages WHERE from_user_id=? OR to_user_id=?
        )''', (user['id'],)*6).fetchall()
    db.close()
    return render_template('messages.html', dialogs=dialogs, active_page='messages')

@app.route('/messages/<int:to_id>', methods=['GET', 'POST'])
def dialog(to_id):
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        painting_id = request.form.get('painting_id') or None
        if content:
            db.execute('INSERT INTO messages (from_user_id, to_user_id, painting_id, content) VALUES (?,?,?,?)',
                (user['id'], to_id, painting_id, content))
            db.commit()
    db.execute('UPDATE messages SET is_read=1 WHERE from_user_id=? AND to_user_id=?', (to_id, user['id']))
    db.commit()
    msgs = db.execute('''SELECT m.*, u.name as sender_name FROM messages m
        LEFT JOIN users u ON m.from_user_id=u.id
        WHERE (from_user_id=? AND to_user_id=?) OR (from_user_id=? AND to_user_id=?)
        ORDER BY m.created_at''', (user['id'], to_id, to_id, user['id'])).fetchall()
    interlocutor = db.execute('SELECT * FROM users WHERE id=?', (to_id,)).fetchone()
    db.close()
    return render_template('dialog.html', messages=msgs, interlocutor=interlocutor)

# ─── Блок 6: Личный кабинет ─────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role     = request.form.get('role', 'buyer')
        if not name or not email or not password:
            flash('Заполните все поля')
            return render_template('register.html')
        db = get_db()
        if db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone():
            flash('Email уже зарегистрирован')
            db.close()
            return render_template('register.html')
        db.execute('INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)',
            (name, email, hash_password(password), role))
        db.commit()
        user = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        db.close()
        session['user_id'] = user['id']
        return redirect(url_for('cabinet'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email=? AND password_hash=?',
            (email, hash_password(password))).fetchone()
        db.close()
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('cabinet'))
        flash('Неверный email или пароль')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/cabinet')
def cabinet():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()
    orders = db.execute('SELECT * FROM orders WHERE buyer_id=? ORDER BY created_at DESC', (user['id'],)).fetchall()
    favorites = db.execute('''SELECT p.*, u.name as artist_name FROM favorites f
        LEFT JOIN paintings p ON f.painting_id=p.id
        LEFT JOIN users u ON p.artist_id=u.id
        WHERE f.user_id=?''', (user['id'],)).fetchall()
    my_paintings = []
    if user['role'] == 'artist':
        my_paintings = db.execute('SELECT * FROM paintings WHERE artist_id=? ORDER BY created_at DESC',
            (user['id'],)).fetchall()
    db.close()
    return render_template('cabinet.html', orders=orders, favorites=favorites,
        my_paintings=my_paintings, active_page='cabinet')

# ─── Блок 7: Избранное ──────────────────────────────────────────────────────

@app.route('/favorite/toggle', methods=['POST'])
def favorite_toggle():
    user = current_user()
    if not user:
        return jsonify({'ok': False, 'error': 'not_logged'})
    pid = request.form.get('painting_id')
    db = get_db()
    fav = db.execute('SELECT id FROM favorites WHERE user_id=? AND painting_id=?',
        (user['id'], pid)).fetchone()
    if fav:
        db.execute('DELETE FROM favorites WHERE user_id=? AND painting_id=?', (user['id'], pid))
        is_fav = False
    else:
        db.execute('INSERT INTO favorites (user_id, painting_id) VALUES (?,?)', (user['id'], pid))
        is_fav = True
    db.commit()
    db.close()
    return jsonify({'ok': True, 'is_favorite': is_fav})

# ─── Блок 9: Аукцион ────────────────────────────────────────────────────────

@app.route('/auctions')
def auctions():
    db = get_db()
    auctions = db.execute('''SELECT a.*, p.title, p.image, u.name as artist_name
        FROM auctions a
        LEFT JOIN paintings p ON a.painting_id=p.id
        LEFT JOIN users u ON p.artist_id=u.id
        WHERE a.status="активен" ORDER BY a.ends_at''').fetchall()
    db.close()
    return render_template('auctions.html', auctions=auctions, active_page='auctions')

@app.route('/auctions/<int:aid>/bid', methods=['POST'])
def auction_bid(aid):
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    amount = float(request.form.get('amount', 0))
    db = get_db()
    auction = db.execute('SELECT * FROM auctions WHERE id=?', (aid,)).fetchone()
    if auction and amount >= auction['current_price'] + auction['min_step']:
        db.execute('INSERT INTO bids (auction_id, user_id, amount) VALUES (?,?,?)',
            (aid, user['id'], amount))
        db.execute('UPDATE auctions SET current_price=? WHERE id=?', (amount, aid))
        db.commit()
    db.close()
    return redirect(url_for('auctions'))

# ─── Запуск ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002, debug=False)
