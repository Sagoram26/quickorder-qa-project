from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..models import User, Order, Restaurant, Product
from ..extensions import db

TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"preparing", "cancelled"},
    "preparing": {"out_for_delivery", "cancelled"},
    "out_for_delivery": {"delivered", "cancelled"},
}

admin_bp = Blueprint("admin", __name__)


def admin_required():
    return current_user.is_authenticated and current_user.role == "admin"


@admin_bp.before_request
def check_admin():
    if not admin_required():
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("main.index"))


@admin_bp.get("/")
@login_required
def dashboard():
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    return render_template("admin.html", users=User.query.count(), orders=Order.query.count(),
                           restaurants=Restaurant.query.count(), products=Product.query.count(),
                           recent_orders=recent_orders)


@admin_bp.post("/orders/<int:order_id>/status")
@login_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    status = request.form.get("status", "").strip()
    allowed = {"confirmed", "preparing", "out_for_delivery", "delivered", "cancelled"}
    if status not in allowed:
        flash("Statut invalide.", "danger")
    else:
        if status not in TRANSITIONS.get(order.status, set()):
            flash(f"Transition de statut invalide ({order.status} → {status}).", "danger")
        else:
            order.status = status
            db.session.commit()
            flash("Statut mis à jour.", "success")
    return redirect(url_for("admin.dashboard"))
