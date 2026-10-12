from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import uuid4
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Order, OrderItem, Coupon, Address, Product
from ..cart import cart_items, clear_cart, add_to_cart

orders_bp = Blueprint("orders", __name__)


def calculate_coupon(coupon_code, subtotal):
    if not coupon_code:
        return None, Decimal("0.00"), None
    coupon = Coupon.query.filter_by(code=coupon_code.strip().upper(), active=True).first()
    if not coupon or (coupon.expires_at and coupon.expires_at < datetime.utcnow()):
        return None, Decimal("0.00"), "Coupon invalide ou expiré."
    if subtotal < coupon.min_order_amount:
        return coupon, Decimal("0.00"), f"Montant minimum de {coupon.min_order_amount:.2f} € requis."
    discount = (subtotal * coupon.discount_percent / 100).quantize(Decimal("0.01"))
    if coupon.max_discount is not None:
        discount = min(discount, coupon.max_discount)
    return coupon, discount, None


def usable_addresses(user_id):
    return Address.query.filter(Address.user_id == user_id, Address.street != "", Address.postal_code != "",
                                Address.city != "").order_by(Address.is_default.desc(), Address.id)


def order_problem(restaurant, lines, subtotal, total, payment, cash_received=None):
    """Retourne un message d'erreur si la commande est refusée, sinon None (UI et API)."""
    if not restaurant.is_open:
        return "Ce restaurant est fermé."
    for product, quantity in lines:
        if quantity > product.stock:
            return f"Stock insuffisant pour {product.name}."
    if subtotal < restaurant.minimum_order:
        return f"Minimum de commande de {restaurant.minimum_order:.2f} € non atteint."
    if payment == "cash":
        try:
            received = Decimal(str(cash_received if cash_received not in (None, "") else "0"))
        except (InvalidOperation, ValueError):
            received = Decimal("0")
        if received < total:
            return "Montant en espèces inférieur au total."
    return None


def build_order(*, user_id, address, restaurant, subtotal, delivery_fee, discount, total,
                payment, customer_note, cash_received=None):
    payment_ok = True
    cash_received_decimal = None
    change_due = None

    if payment == "cash":
        try:
            cash_received_decimal = Decimal(str(cash_received if cash_received not in (None, "") else "0"))
        except (InvalidOperation, ValueError):
            cash_received_decimal = Decimal("0")
        change_due = (cash_received_decimal - total).quantize(Decimal("0.01"))
    order = Order(
        user_id=user_id,
        address_id=address.id,
        restaurant_id=restaurant.id,
        status="confirmed" if payment_ok else "payment_failed",
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        discount=discount,
        total=total,
        payment_status="paid" if payment_ok else "failed",
        payment_method=payment,
        payment_reference=f"PAY-{uuid4().hex[:10].upper()}",
        cash_received=cash_received_decimal,
        change_due=change_due,
        customer_note=customer_note,
    )
    db.session.add(order)
    db.session.flush()
    return order, payment_ok


def add_order_items(order, items):
    for item in items:
        product = item["product"]
        db.session.add(OrderItem(order_id=order.id, product_id=product.id, product_name=product.name,
                                 unit_price=product.price, quantity=item["quantity"],
                                 line_total=item["line_total"]))
        product.stock -= item["quantity"]


@orders_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    items, subtotal = cart_items()
    if not items:
        flash("Votre panier est vide.", "warning")
        return redirect(url_for("shop.cart"))
    restaurant = items[0]["product"].restaurant
    addresses = usable_addresses(current_user.id).all()
    if not addresses:
        flash("Ajoutez une adresse de livraison complète pour commander.", "warning")
        return redirect(url_for("profile.profile"))
    coupon_code = request.form.get("coupon", "").strip().upper() if request.method == "POST" else request.args.get("coupon", "").strip().upper()
    coupon, discount, coupon_error = calculate_coupon(coupon_code, subtotal)
    if coupon_error:
        flash(coupon_error, "warning")
    delivery_fee = restaurant.delivery_fee
    total = max(Decimal("0.00"), subtotal + delivery_fee - discount)

    if request.method == "POST" and request.form.get("confirm") == "1":
        address_id = request.form.get("address_id", type=int)
        address = usable_addresses(current_user.id).filter(Address.id == address_id).first()
        payment = request.form.get("payment_method", "card")
        if not address:
            flash("Adresse de livraison invalide.", "danger")
            return redirect(url_for("orders.checkout"))
        if payment not in {"card", "paypal", "cash"}:
            flash("Mode de paiement invalide.", "danger")
            return redirect(url_for("orders.checkout"))

        cash_received = request.form.get("cash_received") if payment == "cash" else None
        problem = order_problem(restaurant, [(i["product"], i["quantity"]) for i in items], subtotal, total, payment, cash_received)
        if problem:
            flash(problem, "danger")
            return redirect(url_for("orders.checkout"))
        order, payment_ok = build_order(user_id=current_user.id, address=address, restaurant=restaurant,
                                        subtotal=subtotal, delivery_fee=delivery_fee, discount=discount,
                                        total=total, payment=payment,
                                        customer_note=request.form.get("customer_note", "").strip(),
                                        cash_received=cash_received)
        add_order_items(order, items)

        db.session.commit()
        clear_cart()
        flash("Commande confirmée !", "success")
        return redirect(url_for("orders.order_detail", order_id=order.id))

    return render_template("checkout.html", items=items, subtotal=subtotal, delivery_fee=delivery_fee,
                           discount=discount, total=total, coupon_code=coupon_code, addresses=addresses,
                           restaurant=restaurant)


@orders_bp.get("/orders")
@login_required
def order_list():
    status = request.args.get("status", "").strip()
    query = Order.query.filter_by(user_id=current_user.id)
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=orders, status=status)


@orders_bp.route("/orders/<int:order_id>", methods=["GET", "POST"])
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and current_user.role != "admin":
        flash("Commande inaccessible.", "danger")
        return redirect(url_for("orders.order_list"))
    if request.method == "POST" and request.form.get("action") == "cancel":
        if order.status not in {"confirmed", "preparing"}:
            flash("Cette commande ne peut plus être annulée.", "warning")
        else:
            order.status = "cancelled"
            db.session.commit()
            flash("Commande annulée.", "success")
    return render_template("order_detail.html", order=order)


@orders_bp.post("/orders/<int:order_id>/reorder")
@login_required
def reorder(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash("Commande inaccessible.", "danger")
        return redirect(url_for("orders.order_list"))
    clear_cart()
    added = 0
    for item in order.items:
        product = db.session.get(Product, item.product_id)
        if product and product.available and product.stock > 0:
            add_to_cart(product.id, min(item.quantity, product.stock))
            added += 1
    flash(f"{added} produit(s) ajouté(s) au panier.", "success")
    return redirect(url_for("shop.cart"))
