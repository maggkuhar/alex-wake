from database import get_db
from utils import hash_password


def register_user(name, email, password, role):
    db = get_db()
    if db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone():
        db.close()
        return None, 'Email уже зарегистрирован'
    db.execute('INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)',
        (name, email, hash_password(password), role))
    db.commit()
    user = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
    db.close()
    return user, None


def authenticate_user(email, password):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email=? AND password_hash=?',
        (email, hash_password(password))).fetchone()
    db.close()
    return user


def get_cabinet_data(user_id, role):
    db = get_db()
    orders = db.execute('SELECT * FROM orders WHERE buyer_id=? ORDER BY created_at DESC', (user_id,)).fetchall()
    favorites = db.execute('''SELECT p.*, u.name as artist_name FROM favorites f
        LEFT JOIN paintings p ON f.painting_id=p.id
        LEFT JOIN users u ON p.artist_id=u.id
        WHERE f.user_id=?''', (user_id,)).fetchall()
    my_paintings = []
    deposited_ids = []
    if role == 'artist':
        my_paintings = db.execute('SELECT * FROM paintings WHERE artist_id=? ORDER BY created_at DESC',
            (user_id,)).fetchall()
        deposits = db.execute('SELECT painting_id FROM deposits WHERE artist_id=?', (user_id,)).fetchall()
        deposited_ids = [d['painting_id'] for d in deposits]
    db.close()
    return orders, favorites, my_paintings, deposited_ids
