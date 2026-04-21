import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash, send_file
from database import get_db
from utils import current_user, allowed_file
from watermark import apply_watermark, ORIGINALS_DIR
from галерея.logic import (
    get_featured_paintings, get_top_artists, get_catalog, get_painting,
    get_artists, get_artist, get_auctions, place_bid,
    get_painting_by_id, check_purchased, get_themes_and_techniques,
    save_painting, toggle_favorite, get_favorite
)

bp = Blueprint('gallery', __name__, template_folder='templates')


@bp.route('/')
def index():
    featured = get_featured_paintings()
    artists = get_top_artists()
    return render_template('index.html', featured=featured, artists=artists, active_page='catalog')


@bp.route('/catalog')
def catalog():
    theme_id     = request.args.get('theme', '')
    technique_id = request.args.get('technique', '')
    price_min    = request.args.get('price_min', '')
    price_max    = request.args.get('price_max', '')
    sort         = request.args.get('sort', 'new')

    paintings, themes, techniques = get_catalog(theme_id, technique_id, price_min, price_max, sort)
    return render_template('catalog.html', paintings=paintings, themes=themes,
        techniques=techniques, active_page='catalog',
        filters=dict(theme=theme_id, technique=technique_id,
                     price_min=price_min, price_max=price_max, sort=sort))


@bp.route('/painting/<int:pid>')
def painting(pid):
    p, reviews, related = get_painting(pid)
    if not p:
        return redirect(url_for('gallery.catalog'))
    is_favorite = False
    if 'user_id' in session:
        is_favorite = get_favorite(session['user_id'], pid) is not None
    return render_template('painting.html', p=p, reviews=reviews,
        related=related, is_favorite=is_favorite, active_page='catalog')


@bp.route('/artists')
def artists():
    artists = get_artists()
    return render_template('artists.html', artists=artists, active_page='artists')


@bp.route('/artist/<int:uid>')
def artist(uid):
    a, paintings, reviews = get_artist(uid)
    if not a:
        return redirect(url_for('gallery.artists'))
    return render_template('artist.html', a=a, paintings=paintings, reviews=reviews)


@bp.route('/auctions')
def auctions():
    auctions = get_auctions()
    return render_template('auctions.html', auctions=auctions, active_page='auctions')


@bp.route('/auctions/<int:aid>/bid', methods=['POST'])
def auction_bid(aid):
    user = current_user()
    if not user:
        return redirect(url_for('cabinet_bp.login'))
    amount = float(request.form.get('amount', 0))
    place_bid(aid, user['id'], amount)
    return redirect(url_for('gallery.auctions'))


@bp.route('/cabinet/upload', methods=['GET', 'POST'])
def upload_painting():
    user = current_user()
    if not user or user['role'] != 'artist':
        return redirect(url_for('cabinet_bp.login'))
    themes, techniques = get_themes_and_techniques()

    if request.method == 'POST':
        title        = request.form.get('title', '').strip()
        description  = request.form.get('description', '').strip()
        price        = float(request.form.get('price', 0))
        print_price  = request.form.get('print_price', '').strip()
        can_print    = 1 if print_price else 0
        width_cm     = request.form.get('width_cm', '') or None
        height_cm    = request.form.get('height_cm', '') or None
        theme_id     = request.form.get('theme_id', '') or None
        technique_id = request.form.get('technique_id', '') or None
        year         = request.form.get('year', '') or None
        file         = request.files.get('image')

        if not title or not file or not allowed_file(file.filename):
            flash('Заполните название и загрузите изображение (jpg/png)')
            return render_template('upload_painting.html', themes=themes, techniques=techniques)

        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"

        file.save(os.path.join(ORIGINALS_DIR, filename))
        apply_watermark(filename)

        save_painting(user['id'], title, description, price, print_price, can_print,
                      width_cm, height_cm, theme_id, technique_id, year, filename)
        flash('Картина добавлена')
        return redirect(url_for('cabinet_bp.cabinet'))

    return render_template('upload_painting.html', themes=themes, techniques=techniques)


@bp.route('/download/<int:painting_id>')
def download_original(painting_id):
    user = current_user()
    if not user:
        return redirect(url_for('cabinet_bp.login'))
    bought = check_purchased(user['id'], painting_id)
    painting = get_painting_by_id(painting_id)
    if not bought or not painting:
        flash('Доступ запрещён')
        return redirect(url_for('cabinet_bp.cabinet'))
    original_path = os.path.join(ORIGINALS_DIR, painting['image'])
    return send_file(original_path, as_attachment=True, download_name=f"{painting['title']}.jpg")


@bp.route('/favorite/toggle', methods=['POST'])
def favorite_toggle():
    user = current_user()
    if not user:
        return jsonify({'ok': False, 'error': 'not_logged'})
    pid = request.form.get('painting_id')
    is_fav = toggle_favorite(user['id'], pid)
    return jsonify({'ok': True, 'is_favorite': is_fav})
