from database import get_db


def get_my_paintings_with_deposit(artist_id):
    db = get_db()
    result = db.execute('''SELECT p.*, d.status as deposit_status
        FROM paintings p
        LEFT JOIN deposits d ON d.painting_id = p.id
        WHERE p.artist_id=? ORDER BY p.created_at DESC''', (artist_id,)).fetchall()
    db.close()
    return result


def create_deposit(painting_id, artist_id, artist_full_name, passport, description):
    db = get_db()
    db.execute('''INSERT OR IGNORE INTO deposits
        (painting_id, artist_id, artist_full_name, passport_data, description, status)
        VALUES (?,?,?,?,?,"новая")''',
        (painting_id, artist_id, artist_full_name, passport, description))
    db.commit()
    db.close()
