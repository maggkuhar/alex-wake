from database import get_db


def get_cart_paintings(cart):
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
    return paintings, total


def get_dialogs(user_id):
    db = get_db()
    dialogs = db.execute('''SELECT u.id, u.name, u.avatar, u.role,
        (SELECT content FROM messages
         WHERE (from_user_id=u.id AND to_user_id=?) OR (from_user_id=? AND to_user_id=u.id)
         ORDER BY created_at DESC LIMIT 1) as last_msg,
        (SELECT COUNT(*) FROM messages WHERE from_user_id=u.id AND to_user_id=? AND is_read=0) as unread
        FROM users u WHERE u.id IN (
            SELECT DISTINCT CASE WHEN from_user_id=? THEN to_user_id ELSE from_user_id END
            FROM messages WHERE from_user_id=? OR to_user_id=?
        )''', (user_id,)*6).fetchall()
    db.close()
    return dialogs


def get_dialog_messages(user_id, to_id, content=None, painting_id=None):
    db = get_db()
    if content:
        db.execute('INSERT INTO messages (from_user_id, to_user_id, painting_id, content) VALUES (?,?,?,?)',
            (user_id, to_id, painting_id, content))
        db.commit()
    db.execute('UPDATE messages SET is_read=1 WHERE from_user_id=? AND to_user_id=?', (to_id, user_id))
    db.commit()
    msgs = db.execute('''SELECT m.*, u.name as sender_name FROM messages m
        LEFT JOIN users u ON m.from_user_id=u.id
        WHERE (from_user_id=? AND to_user_id=?) OR (from_user_id=? AND to_user_id=?)
        ORDER BY m.created_at''', (user_id, to_id, to_id, user_id)).fetchall()
    interlocutor = db.execute('SELECT * FROM users WHERE id=?', (to_id,)).fetchone()
    db.close()
    return msgs, interlocutor
