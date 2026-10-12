from sqlalchemy import or_
from flask import Blueprint, render_template, request
from flask_login import current_user
from ..models import Restaurant, Product, Favorite

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    vegetarian = request.args.get("vegetarian") == "1"
    max_delivery = request.args.get("max_delivery", type=float)
    sort = request.args.get("sort", "rating")

    query = Restaurant.query
    if q:
        query = query.filter(or_(Restaurant.name.ilike(f"%{q}%"), Restaurant.description.ilike(f"%{q}%")))
    if category:
        query = query.filter_by(category=category)
    if max_delivery is not None:
        query = query.filter(Restaurant.delivery_fee <= max_delivery)
    if sort == "price":
        query = query.order_by(Restaurant.delivery_fee.asc())
    elif sort == "time":
        query = query.order_by(Restaurant.delivery_time_min.asc())
    else:
        query = query.order_by(Restaurant.rating.desc())
    restaurants = query.all()
    if vegetarian:
        restaurants = [r for r in restaurants if any(p.is_vegetarian and p.available for p in r.products)]
    categories = [c[0] for c in Restaurant.query.with_entities(Restaurant.category).distinct().order_by(Restaurant.category).all()]
    favorite_ids = set()
    if current_user.is_authenticated:
        favorite_ids = {f.restaurant_id for f in Favorite.query.filter_by(user_id=current_user.id).all()}
    return render_template("index.html", restaurants=restaurants, categories=categories, q=q,
                           category=category, vegetarian=vegetarian, max_delivery=max_delivery, sort=sort,
                           favorite_ids=favorite_ids)


@main_bp.route("/restaurant/<int:restaurant_id>")
def restaurant(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    category = request.args.get("category", "").strip()
    q = request.args.get("q", "").strip()
    # stock=0 reste visible mais non commandable (bouton désactivé dans le template).
    products_query = Product.query.filter_by(restaurant_id=restaurant.id, available=True)
    if category:
        products_query = products_query.filter_by(category=category)
    if q:
        products_query = products_query.filter(Product.name.ilike(f"%{q}%"))
    products = products_query.order_by(Product.category, Product.name).all()
    categories = [c[0] for c in Product.query.with_entities(Product.category).filter_by(restaurant_id=restaurant.id).distinct().all()]
    is_favorite = False
    if current_user.is_authenticated:
        is_favorite = Favorite.query.filter_by(user_id=current_user.id, restaurant_id=restaurant.id).first() is not None
    return render_template("restaurant.html", restaurant=restaurant, products=products, categories=categories,
                           selected_category=category, q=q, is_favorite=is_favorite)


@main_bp.get("/health")
def health():
    return {"status": "ok", "service": "quickorder"}
