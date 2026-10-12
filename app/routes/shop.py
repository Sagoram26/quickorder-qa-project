from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..cart import get_cart, add_to_cart, update_cart, cart_items, clear_cart, remove_from_cart, cart_restaurant_ids
from ..models import Product, Restaurant, Favorite, Review, Order
from ..extensions import db

shop_bp = Blueprint("shop", __name__)


@shop_bp.post("/cart/add/<int:product_id>")
def add(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = request.form.get("quantity", 1, type=int)
    quantity = max(quantity or 1, 1)

    if not product.available or product.stock <= 0:
        flash("Produit indisponible.", "danger")
        return redirect(request.referrer or url_for("main.index"))
    if not product.restaurant.is_open:
        flash("Ce restaurant est fermé.", "danger")
        return redirect(request.referrer or url_for("main.index"))
    existing_restaurants = cart_restaurant_ids()
    if existing_restaurants and product.restaurant_id not in existing_restaurants:
        flash("Un panier ne peut contenir que des produits du même restaurant.", "warning")
        return redirect(request.referrer or url_for("main.index"))
    in_cart = get_cart().get(str(product.id), 0)
    if in_cart + quantity > product.stock:
        quantity = product.stock - in_cart
        flash(f"Quantité limitée au stock disponible ({product.stock}).", "warning")
        if quantity <= 0:
            return redirect(request.referrer or url_for("main.index"))
    add_to_cart(product.id, quantity)
    flash(f"{product.name} ajouté au panier.", "success")
    return redirect(request.referrer or url_for("main.index"))


@shop_bp.route("/cart", methods=["GET", "POST"])
def cart():
    if request.method == "POST":
        for product_id, quantity in request.form.items():
            if product_id.startswith("qty_"):
                try:
                    product = db.session.get(Product, int(product_id.replace("qty_", "")))
                    stock = product.stock if product else 0
                    if int(quantity) > stock:
                        flash(f"Quantité limitée au stock disponible ({stock}).", "warning")
                    update_cart(product_id.replace("qty_", ""), min(int(quantity), stock))
                except ValueError:
                    flash("Quantité invalide.", "danger")
    items, subtotal = cart_items()
    delivery_fee = items[0]["product"].restaurant.delivery_fee if items else 0
    total = subtotal + delivery_fee if items else 0
    return render_template("cart.html", items=items, subtotal=subtotal, delivery_fee=delivery_fee, total=total)


@shop_bp.post("/cart/remove/<int:product_id>")
def remove(product_id):
    remove_from_cart(product_id)
    flash("Produit retiré du panier.", "info")
    return redirect(url_for("shop.cart"))


@shop_bp.post("/cart/clear")
def clear():
    clear_cart()
    flash("Panier vidé.", "info")
    return redirect(url_for("shop.cart"))


@shop_bp.post("/favorite/<int:restaurant_id>")
@login_required
def toggle_favorite(restaurant_id):
    Restaurant.query.get_or_404(restaurant_id)
    favorite = Favorite.query.filter_by(user_id=current_user.id, restaurant_id=restaurant_id).first()
    if favorite:
        db.session.delete(favorite)
        flash("Restaurant retiré des favoris.", "info")
    else:
        db.session.add(Favorite(user_id=current_user.id, restaurant_id=restaurant_id))
        flash("Restaurant ajouté aux favoris.", "success")
    db.session.commit()
    return redirect(request.referrer or url_for("main.index"))


@shop_bp.post("/restaurant/<int:restaurant_id>/review")
@login_required
def review(restaurant_id):
    Restaurant.query.get_or_404(restaurant_id)
    delivered = Order.query.filter_by(user_id=current_user.id, restaurant_id=restaurant_id, status="delivered").first()
    if not delivered:
        flash("Vous ne pouvez noter qu'un restaurant où une commande vous a été livrée.", "danger")
        return redirect(url_for("main.restaurant", restaurant_id=restaurant_id))
    try:
        rating = int(request.form.get("rating", 0))
    except ValueError:
        rating = 0
    comment = request.form.get("comment", "").strip()
    if rating not in range(1, 6) or not comment:
        flash("Note et commentaire obligatoires.", "danger")
        return redirect(request.referrer or url_for("main.restaurant", restaurant_id=restaurant_id))
    db.session.add(Review(user_id=current_user.id, restaurant_id=restaurant_id, rating=rating, comment=comment))
    db.session.commit()
    flash("Merci pour votre avis !", "success")
    return redirect(url_for("main.restaurant", restaurant_id=restaurant_id))
