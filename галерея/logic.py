from database import get_db


def get_featured_paintings(limit=8):
    db = get_db()
    result = db.execute('''SELECT p.*, u.name as artist_name FROM paintings p
        LEFT JOIN users u ON p.artist_id = u.id
        WHERE p.in_stock=1 ORDER BY p.rating DESC, p.views DESC LIMIT ?''', (limit,)).fetchall()
    db.close()
    return result


def get_top_artists(limit=6):
    db = get_db()
    result = db.execute('''SELECT * FROM users WHERE role="artist"
        ORDER BY rating DESC LIMIT ?''', (limit,)).fetchall()
    db.close()
    return result


def get_catalog(theme_id='', technique_id='', price_min='', price_max='', sort='new'):
    db = get_db()
    themes = db.execute('SELECT * FROM themes ORDER BY name').fetchall()
    techniques = db.execute('SELECT * FROM techniques ORDER BY name').fetchall()

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
    return paintings, themes, techniques


def get_painting(pid):
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
    related = []
    if p:
        related = db.execute('''SELECT p.*, u.name as artist_name FROM paintings p
            LEFT JOIN users u ON p.artist_id=u.id
            WHERE p.theme_id=? AND p.id!=? AND p.in_stock=1 LIMIT 4''',
            (p['theme_id'], pid)).fetchall()
    db.close()
    return p, reviews, related


def get_artists():
    db = get_db()
    result = db.execute('''SELECT u.*,
        COUNT(p.id) as paintings_count FROM users u
        LEFT JOIN paintings p ON p.artist_id=u.id
        WHERE u.role="artist" GROUP BY u.id
        ORDER BY u.rating DESC''').fetchall()
    db.close()
    return result


def get_artist(uid):
    db = get_db()
    a = db.execute('SELECT * FROM users WHERE id=? AND role="artist"', (uid,)).fetchone()
    paintings = db.execute('''SELECT * FROM paintings WHERE artist_id=?
        ORDER BY created_at DESC''', (uid,)).fetchall()
    reviews = db.execute('''SELECT r.*, u.name as user_name FROM reviews r
        LEFT JOIN users u ON r.user_id=u.id
        WHERE r.artist_id=? ORDER BY r.created_at DESC''', (uid,)).fetchall()
    db.close()
    return a, paintings, reviews


def get_auctions():
    db = get_db()
    result = db.execute('''SELECT a.*, p.title, p.image, u.name as artist_name
        FROM auctions a
        LEFT JOIN paintings p ON a.painting_id=p.id
        LEFT JOIN users u ON p.artist_id=u.id
        WHERE a.status="активен" ORDER BY a.ends_at''').fetchall()
    db.close()
    return result


def place_bid(aid, user_id, amount):
    db = get_db()
    auction = db.execute('SELECT * FROM auctions WHERE id=?', (aid,)).fetchone()
    if auction and amount >= auction['current_price'] + auction['min_step']:
        db.execute('INSERT INTO bids (auction_id, user_id, amount) VALUES (?,?,?)',
            (aid, user_id, amount))
        db.execute('UPDATE auctions SET current_price=? WHERE id=?', (amount, aid))
        db.commit()
    db.close()


def get_painting_by_id(painting_id):
    db = get_db()
    result = db.execute('SELECT * FROM paintings WHERE id=?', (painting_id,)).fetchone()
    db.close()
    return result


def check_purchased(user_id, painting_id):
    db = get_db()
    result = db.execute('''SELECT oi.id FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.buyer_id=? AND oi.painting_id=? AND o.payment_status="оплачен"''',
        (user_id, painting_id)).fetchone()
    db.close()
    return result


def get_themes_and_techniques():
    db = get_db()
    themes = db.execute('SELECT * FROM themes ORDER BY name').fetchall()
    techniques = db.execute('SELECT * FROM techniques ORDER BY name').fetchall()
    db.close()
    return themes, techniques


def save_painting(user_id, title, description, price, print_price, can_print,
                  width_cm, height_cm, theme_id, technique_id, year, filename):
    db = get_db()
    db.execute('''INSERT INTO paintings
        (artist_id, title, description, price, print_price, can_print,
         width_cm, height_cm, theme_id, technique_id, year, image)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
        (user_id, title, description, price,
         float(print_price) if print_price else None,
         can_print, width_cm, height_cm, theme_id, technique_id, year, filename))
    db.commit()
    db.close()


def get_favorite(user_id, painting_id):
    db = get_db()
    result = db.execute('SELECT id FROM favorites WHERE user_id=? AND painting_id=?',
        (user_id, painting_id)).fetchone()
    db.close()
    return result


def toggle_favorite(user_id, painting_id):
    db = get_db()
    fav = db.execute('SELECT id FROM favorites WHERE user_id=? AND painting_id=?',
        (user_id, painting_id)).fetchone()
    if fav:
        db.execute('DELETE FROM favorites WHERE user_id=? AND painting_id=?', (user_id, painting_id))
        is_fav = False
    else:
        db.execute('INSERT INTO favorites (user_id, painting_id) VALUES (?,?)', (user_id, painting_id))
        is_fav = True
    db.commit()
    db.close()
    return is_fav
