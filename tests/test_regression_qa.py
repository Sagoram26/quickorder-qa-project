"""Non-régression des bugs QA (docs/bug-reports/BUG-001..016)."""
from pathlib import Path
from app.extensions import db
from app.models import Order, Product, Restaurant, User, Review, Address

KEY = {"X-API-Key": "quickorder-demo-key"}


def api_order(client, pid, qty=1, **extra):
    return client.post("/api/orders", headers=KEY, json={"items": [{"product_id": pid, "quantity": qty}], **extra})


def checkout(client, **extra):
    data = {"confirm": "1", "address_id": 1, "payment_method": "card", **extra}
    return client.post("/checkout", data=data)


def n_orders(app):
    with app.app_context():
        return Order.query.count()


def test_bug001_stock_zero_refused(logged):
    logged.post("/cart/add/2", data={"quantity": 1})
    assert b"Rupture" not in logged.get("/cart").data


def test_bug002_quantity_capped_and_revalidated(app, logged):
    logged.post("/cart/add/1", data={"quantity": 50})
    assert b'value="10"' in logged.get("/cart").data or b"10" in logged.get("/cart").data
    assert api_order(logged, 1, 11).status_code == 409
    with app.app_context():
        db.session.get(Product, 1).stock = 2
        db.session.commit()
    checkout(logged)  # panier = 10 > stock 2
    assert n_orders(app) == 0


def test_bug003_closed_restaurant_refused(app, logged):
    logged.post("/cart/add/3", data={"quantity": 1})
    assert b"Closed Dish" not in logged.get("/cart").data
    assert api_order(logged, 3).status_code == 409


def test_bug004_minimum_order(app, logged):
    with app.app_context():
        db.session.get(Restaurant, 1).minimum_order = 50
        db.session.commit()
    logged.post("/cart/add/1", data={"quantity": 1})
    checkout(logged)
    assert n_orders(app) == 0
    assert api_order(logged, 1).status_code == 409


def test_bug005_cash_insufficient(app, logged):
    logged.post("/cart/add/1", data={"quantity": 1})
    checkout(logged, payment_method="cash", cash_received="5")
    assert n_orders(app) == 0
    assert api_order(logged, 1, payment_method="cash", cash_received=5).status_code == 409
    assert api_order(logged, 1, payment_method="cash", cash_received=50).status_code == 201


def test_bug006_paypal_single_order(app, logged):
    assert api_order(logged, 1, payment_method="paypal").status_code == 201
    logged.post("/cart/add/1", data={"quantity": 1})
    checkout(logged, payment_method="paypal")
    assert n_orders(app) == 2


def test_bug007_atlas15_seed_is_15_percent():
    seed = (Path(__file__).parent.parent / "seed.py").read_text(encoding="utf-8")
    assert 'code="ATLAS15", discount_percent=Decimal("15")' in seed


def test_bug008_max_delivery_inclusive_and_correct(client):
    # Test Restaurant : livraison 2.99, Closed : 2.99 (défaut)
    assert b"Test Restaurant" not in client.get("/?max_delivery=2.50").data
    assert b"Test Restaurant" in client.get("/?max_delivery=2.99").data


def test_bug009_no_backward_transition(app, client):
    with app.app_context():
        admin = User(name="Admin", email="a@x.io", role="admin")
        admin.set_password("Admin123!")
        db.session.add(admin)
        db.session.add(Order(user_id=1, restaurant_id=1, status="delivered", subtotal=1, delivery_fee=0, total=1))
        db.session.commit()
    client.post("/login", data={"email": "a@x.io", "password": "Admin123!"})
    client.post("/admin/orders/1/status", data={"status": "confirmed"})
    with app.app_context():
        assert db.session.get(Order, 1).status == "delivered"


def test_bug010_review_needs_delivered_order(app, logged):
    logged.post("/restaurant/1/review", data={"rating": 1, "comment": "x"})
    with app.app_context():
        assert Review.query.count() == 0
        db.session.add(Order(user_id=1, restaurant_id=1, status="delivered", subtotal=1, delivery_fee=0, total=1))
        db.session.commit()
    logged.post("/restaurant/1/review", data={"rating": 5, "comment": "ok"})
    with app.app_context():
        assert Review.query.count() == 1


def test_bug011_next_must_be_internal(client):
    form = {"email": "test@example.com", "password": "Password123!"}
    r = client.post("/login?next=https://evil.example/x", data=form)
    assert r.headers["Location"] == "/"
    client.post("/logout")
    r = client.post("/login?next=//evil.example", data=form)
    assert r.headers["Location"] == "/"
    client.post("/logout")
    assert client.post("/login?next=/orders", data=form).headers["Location"] == "/orders"


def test_bug012_api_requires_session(client):
    assert client.post("/api/orders", headers=KEY, json={"items": [{"product_id": 1, "quantity": 1}]}).status_code == 401
    assert client.get("/api/orders", headers=KEY).status_code == 401


def test_bug014_search_includes_description(client):
    assert b"Closed" in client.get("/?q=Ferme").data
    assert client.get("/api/restaurants?q=Ferme", headers=KEY).get_json()["count"] == 1


def test_bug015_no_empty_address_and_checkout_requires_one(app, client):
    client.post("/register", data={"name": "New User", "email": "n@x.io", "password": "Password123!"})
    with app.app_context():
        uid = User.query.filter_by(email="n@x.io").first().id
        assert Address.query.filter_by(user_id=uid).count() == 0
    client.post("/cart/add/1", data={"quantity": 1})
    r = client.get("/checkout")
    assert r.status_code == 302 and "/profile" in r.headers["Location"]


def test_bug016_logout_is_post_only(logged):
    assert logged.get("/logout").status_code == 405
    assert b"Mon profil" in logged.get("/profile/").data
    logged.post("/logout")
    assert logged.get("/profile/").status_code == 302
