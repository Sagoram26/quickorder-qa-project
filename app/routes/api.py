from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from uuid import uuid4
from sqlalchemy import or_
from flask import Blueprint, jsonify, request, current_app, g
from flask_login import current_user
from ..models import Restaurant, Product, Order, OrderItem, Coupon, Favorite, User, Address
from ..extensions import db
from .orders import order_problem, usable_addresses

api_bp = Blueprint("api", __name__)


def money(value):
    return float(value or 0)


def api_key_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Students can discover this header from Swagger's Authorize button.
        if request.headers.get("X-API-Key") != current_app.config.get("API_KEY", "quickorder-demo-key"):
            return jsonify({"error": "missing or invalid X-API-Key", "hint": "Use Swagger > Authorize"}), 401
        return fn(*args, **kwargs)
    return wrapper


def session_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "authentication required (login session)"}), 401
        return fn(*args, **kwargs)
    return wrapper


def api_customer():
    return current_user


def restaurant_json(r):
    return {"id": r.id, "name": r.name, "description": r.description, "promo_text": r.promo_text,
            "category": r.category, "address": r.address, "delivery_fee": money(r.delivery_fee),
            "minimum_order": money(r.minimum_order), "delivery_time_min": r.delivery_time_min,
            "rating": money(r.rating), "is_open": r.is_open}


def product_json(p):
    return {"id": p.id, "restaurant_id": p.restaurant_id, "name": p.name, "description": p.description,
            "category": p.category, "price": money(p.price), "available": p.available, "stock": p.stock,
            "calories": p.calories, "is_vegetarian": p.is_vegetarian}


def order_json(order):
    return {"id": order.id, "restaurant_id": order.restaurant_id, "status": order.status,
            "payment_status": order.payment_status, "payment_method": order.payment_method,
            "cash_received": money(order.cash_received) if order.cash_received is not None else None,
            "change_due": money(order.change_due) if order.change_due is not None else None,
            "subtotal": money(order.subtotal), "delivery_fee": money(order.delivery_fee),
            "discount": money(order.discount), "total": money(order.total),
            "created_at": order.created_at.isoformat(),
            "items": [{"product_id": i.product_id, "product_name": i.product_name, "unit_price": money(i.unit_price),
                       "quantity": i.quantity, "line_total": money(i.line_total)} for i in order.items]}


@api_bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": "quickorder", "timestamp": datetime.utcnow().isoformat()})


@api_bp.get("/restaurants")
@api_key_required
def restaurants():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    min_rating = request.args.get("min_rating", type=float)
    query = Restaurant.query
    if q:
        query = query.filter(or_(Restaurant.name.ilike(f"%{q}%"), Restaurant.description.ilike(f"%{q}%")))
    if category:
        query = query.filter_by(category=category)
    if min_rating is not None:
        query = query.filter(Restaurant.rating >= min_rating)
    # INTENTIONAL QA BUG: API exposes closed restaurants even though the main UI
    # describes the list as orderable restaurants.
    return jsonify({"count": query.count(), "items": [restaurant_json(r) for r in query.order_by(Restaurant.rating.desc()).all()]})


@api_bp.get("/restaurants/<int:restaurant_id>")
@api_key_required
def restaurant_detail(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    return jsonify(restaurant_json(restaurant))


@api_bp.get("/restaurants/<int:restaurant_id>/products")
@api_key_required
def restaurant_products(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    category = request.args.get("category", "").strip()
    vegetarian = request.args.get("vegetarian") == "true"
    query = Product.query.filter_by(restaurant_id=restaurant.id)
    if category:
        query = query.filter_by(category=category)
    if vegetarian:
        query = query.filter_by(is_vegetarian=True)
    return jsonify({"restaurant": restaurant_json(restaurant), "items": [product_json(p) for p in query.order_by(Product.category, Product.name).all()]})


@api_bp.get("/products/<int:product_id>")
@api_key_required
def product_detail(product_id):
    return jsonify(product_json(Product.query.get_or_404(product_id)))


@api_bp.post("/coupons/validate")
@api_key_required
def validate_coupon():
    payload = request.get_json(silent=True) or {}
    code = str(payload.get("code", "")).strip().upper()
    try:
        # INTENTIONAL QA BUG: the API trusts the subtotal supplied by the client.
        subtotal = Decimal(str(payload.get("subtotal", 0)))
    except (InvalidOperation, ValueError):
        return jsonify({"valid": False, "error": "subtotal must be numeric"}), 400
    coupon = Coupon.query.filter_by(code=code, active=True).first()
    if not coupon or (coupon.expires_at and coupon.expires_at < datetime.utcnow()):
        return jsonify({"valid": False, "error": "Coupon invalide ou expiré."}), 404
    if subtotal < coupon.min_order_amount:
        return jsonify({"valid": False, "error": "Montant minimum non atteint.", "minimum": money(coupon.min_order_amount)}), 200
    discount = (subtotal * coupon.discount_percent / 100).quantize(Decimal("0.01"))
    if coupon.max_discount is not None:
        discount = min(discount, coupon.max_discount)
    return jsonify({"valid": True, "code": coupon.code, "discount": money(discount),
                    "discount_percent": money(coupon.discount_percent)})


@api_bp.post("/orders")
@api_key_required
@session_required
def create_order_api():
    payload = request.get_json(silent=True) or {}
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        return jsonify({"error": "items is required and must be a non-empty array"}), 400
    product_ids = [item.get("product_id") for item in items if isinstance(item, dict)]
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    by_id = {p.id: p for p in products}
    if len(by_id) != len(set(product_ids)):
        return jsonify({"error": "one or more products do not exist"}), 400
    restaurant_ids = {p.restaurant_id for p in products}
    if len(restaurant_ids) != 1:
        return jsonify({"error": "all products must belong to the same restaurant"}), 400
    normalized = []
    subtotal = Decimal("0.00")
    for item in items:
        try:
            quantity = int(item.get("quantity", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "quantity must be an integer"}), 400
        if quantity < 1 or quantity > 20:
            return jsonify({"error": "quantity must be between 1 and 20"}), 400
        product = by_id[item["product_id"]]
        if not product.available:
            return jsonify({"error": f"product {product.id} is unavailable"}), 409
        line_total = product.price * quantity
        subtotal += line_total
        normalized.append((product, quantity, line_total))
    restaurant = products[0].restaurant
    discount = Decimal("0.00")
    code = str(payload.get("coupon", "")).strip().upper()
    if code:
        coupon = Coupon.query.filter_by(code=code, active=True).first()
        if coupon and subtotal >= coupon.min_order_amount:
            discount = (subtotal * coupon.discount_percent / 100).quantize(Decimal("0.01"))
            if coupon.max_discount is not None:
                discount = min(discount, coupon.max_discount)
    delivery_fee = restaurant.delivery_fee
    total = max(Decimal("0.00"), subtotal + delivery_fee - discount)
    payment_method = payload.get("payment_method", "card")
    if payment_method not in {"card", "paypal", "cash"}:
        return jsonify({"error": "invalid payment_method"}), 400
    address = usable_addresses(api_customer().id).first()
    if not address:
        return jsonify({"error": "no delivery address"}), 400
    cash_received = payload.get("cash_received") if payment_method == "cash" else None
    problem = order_problem(restaurant, [(p, q) for p, q, _ in normalized], subtotal, total, payment_method, cash_received)
    if problem:
        return jsonify({"error": problem}), 409
    try:
        cash_received_decimal = Decimal(str(cash_received)) if cash_received is not None else None
    except InvalidOperation:
        cash_received_decimal = Decimal("0")
    change_due = (cash_received_decimal - total).quantize(Decimal("0.01")) if cash_received_decimal is not None else None
    order = Order(user_id=api_customer().id, address_id=address.id, restaurant_id=restaurant.id, status="confirmed",
                  subtotal=subtotal, delivery_fee=delivery_fee, discount=discount, total=total,
                  payment_status="paid", payment_method=payment_method,
                  payment_reference=f"API-{uuid4().hex[:10].upper()}", cash_received=cash_received_decimal,
                  change_due=change_due)
    db.session.add(order)
    db.session.flush()
    for product, quantity, line_total in normalized:
        db.session.add(OrderItem(order_id=order.id, product_id=product.id, product_name=product.name,
                                 unit_price=product.price, quantity=quantity, line_total=line_total))
        product.stock -= quantity
    db.session.commit()
    return jsonify(order_json(order)), 201


@api_bp.get("/orders")
@api_key_required
@session_required
def list_orders():
    status = request.args.get("status", "").strip()
    query = Order.query.filter_by(user_id=api_customer().id)
    if status:
        query = query.filter_by(status=status)
    return jsonify({"count": query.count(), "items": [order_json(o) for o in query.order_by(Order.created_at.desc()).all()]})


@api_bp.get("/orders/<int:order_id>")
@api_key_required
@session_required
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != api_customer().id and api_customer().role != "admin":
        return jsonify({"error": "forbidden"}), 403
    return jsonify(order_json(order))


@api_bp.post("/orders/<int:order_id>/cancel")
@api_key_required
@session_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != api_customer().id and api_customer().role != "admin":
        return jsonify({"error": "forbidden"}), 403
    if order.status not in {"confirmed", "preparing"}:
        return jsonify({"error": "order cannot be cancelled", "status": order.status}), 409
    order.status = "cancelled"
    db.session.commit()
    return jsonify(order_json(order))


@api_bp.get("/favorites")
@api_key_required
@session_required
def favorites():
    favorites = Favorite.query.filter_by(user_id=api_customer().id).all()
    return jsonify({"items": [restaurant_json(f.restaurant) for f in favorites]})
