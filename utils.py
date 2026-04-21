import hashlib
from flask import session
from database import get_db

ALLOWED = {'jpg', 'jpeg', 'png', 'webp'}

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def current_user():
    if 'user_id' not in session:
        return None
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    db.close()
    return user

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED
