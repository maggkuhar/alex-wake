import os
import sys

# Добавляем корень проекта в путь поиска модулей
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, session
from database import init_db

from галерея.routes import bp as bp_gallery
from кабинет.routes import bp as bp_cabinet
from продажи.routes import bp as bp_sales
from депонирование.routes import bp as bp_deposit

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'alexwake-secret-key')


@app.context_processor
def inject_globals():
    from utils import current_user
    user = current_user()
    cart = session.get('cart', {})
    cart_count = sum(cart.values())
    return dict(user=user, cart_count=cart_count)


app.register_blueprint(bp_gallery)
app.register_blueprint(bp_cabinet)
app.register_blueprint(bp_sales)
app.register_blueprint(bp_deposit)


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002, debug=False)
