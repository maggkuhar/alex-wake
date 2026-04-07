import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'alexwake.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    # Пользователи (роли: buyer / artist / admin)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'buyer',
        avatar TEXT,
        bio TEXT,
        city TEXT,
        website TEXT,
        telegram TEXT,
        rating REAL DEFAULT 0,
        rating_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )''')

    # Тематики
    conn.execute('''CREATE TABLE IF NOT EXISTS themes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL
    )''')

    # Техники
    conn.execute('''CREATE TABLE IF NOT EXISTS techniques (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL
    )''')

    # Картины
    conn.execute('''CREATE TABLE IF NOT EXISTS paintings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        artist_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        image TEXT,
        price REAL NOT NULL,
        old_price REAL,
        width_cm INTEGER,
        height_cm INTEGER,
        theme_id INTEGER,
        technique_id INTEGER,
        style TEXT,
        year INTEGER,
        is_original INTEGER DEFAULT 1,
        can_print INTEGER DEFAULT 0,
        in_stock INTEGER DEFAULT 1,
        auction_mode INTEGER DEFAULT 0,
        views INTEGER DEFAULT 0,
        rating REAL DEFAULT 0,
        rating_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (artist_id) REFERENCES users(id),
        FOREIGN KEY (theme_id) REFERENCES themes(id),
        FOREIGN KEY (technique_id) REFERENCES techniques(id)
    )''')

    # Избранное
    conn.execute('''CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        painting_id INTEGER NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(user_id, painting_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (painting_id) REFERENCES paintings(id)
    )''')

    # Отзывы
    conn.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        painting_id INTEGER,
        artist_id INTEGER,
        rating INTEGER NOT NULL,
        text TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (painting_id) REFERENCES paintings(id),
        FOREIGN KEY (artist_id) REFERENCES users(id)
    )''')

    # Заказы
    conn.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        buyer_id INTEGER NOT NULL,
        status TEXT DEFAULT 'новый',
        total REAL NOT NULL,
        delivery_name TEXT,
        delivery_phone TEXT,
        delivery_address TEXT,
        delivery_city TEXT,
        payment_method TEXT,
        payment_status TEXT DEFAULT 'не оплачен',
        comment TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (buyer_id) REFERENCES users(id)
    )''')

    # Позиции заказа
    conn.execute('''CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        painting_id INTEGER NOT NULL,
        type TEXT DEFAULT 'original',
        quantity INTEGER DEFAULT 1,
        price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (painting_id) REFERENCES paintings(id)
    )''')

    # Аукционы
    conn.execute('''CREATE TABLE IF NOT EXISTS auctions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        painting_id INTEGER NOT NULL,
        start_price REAL NOT NULL,
        current_price REAL NOT NULL,
        min_step REAL DEFAULT 100,
        ends_at TEXT NOT NULL,
        winner_id INTEGER,
        status TEXT DEFAULT 'активен',
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (painting_id) REFERENCES paintings(id),
        FOREIGN KEY (winner_id) REFERENCES users(id)
    )''')

    # Ставки аукциона
    conn.execute('''CREATE TABLE IF NOT EXISTS bids (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auction_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (auction_id) REFERENCES auctions(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Чат
    conn.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user_id INTEGER NOT NULL,
        to_user_id INTEGER NOT NULL,
        painting_id INTEGER,
        content TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (from_user_id) REFERENCES users(id),
        FOREIGN KEY (to_user_id) REFERENCES users(id),
        FOREIGN KEY (painting_id) REFERENCES paintings(id)
    )''')

    # Депонирование
    conn.execute('''CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        painting_id INTEGER NOT NULL UNIQUE,
        artist_id INTEGER NOT NULL,
        artist_full_name TEXT NOT NULL,
        passport_data TEXT,
        description TEXT,
        status TEXT DEFAULT 'новая',
        certificate_file TEXT,
        edrid_number TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (painting_id) REFERENCES paintings(id),
        FOREIGN KEY (artist_id) REFERENCES users(id)
    )''')

    # Добавляем print_price если нет
    try:
        conn.execute('ALTER TABLE paintings ADD COLUMN print_price REAL')
    except:
        pass

    # Подписки на художников/тематики
    conn.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        artist_id INTEGER,
        theme_id INTEGER,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (artist_id) REFERENCES users(id),
        FOREIGN KEY (theme_id) REFERENCES themes(id)
    )''')

    # Начальные тематики
    themes = ['Пейзаж','Портрет','Абстракция','Натюрморт','Животные',
              'Город','Море','Люди','Фэнтези','Минимализм',
              'Цветы','Обнажённая натура','Религия','История']
    for t in themes:
        slug = t.lower().replace(' ', '_').replace('ё','е')
        conn.execute("INSERT OR IGNORE INTO themes (name, slug) VALUES (?,?)", (t, slug))

    # Начальные техники
    techniques = ['Масло','Акварель','Акрил','Пастель','Графит',
                  'Уголь','Тушь','Гуашь','Темпера','Цифровая']
    for t in techniques:
        slug = t.lower().replace(' ', '_')
        conn.execute("INSERT OR IGNORE INTO techniques (name, slug) VALUES (?,?)", (t, slug))

    conn.commit()
    conn.close()
