from datetime import datetime, timedelta
from decimal import Decimal
from app import create_app
from app.extensions import db
from app.models import User, Restaurant, Product, Coupon, Address, Order, OrderItem, Review

app = create_app()

restaurants_data = [
    ("Burger Factory", "Burgers, frites et menus généreux.", "", "Burgers", "18 rue du Commerce, Paris", "2.99", "20.00", 25, "4.7", [
        ("Classic Burger", "Bœuf, cheddar, salade, sauce maison", "Burgers", "11.90", 720, False, 100),
        ("Double Cheese", "Double steak, double cheddar", "Burgers", "14.90", 910, False, 100),
        ("Frites maison", "Frites croustillantes", "Accompagnements", "3.50", 420, True, 100),
        ("Veggie Burger", "Steak végétal, tomate, salade, sauce", "Burgers", "12.90", 610, True, 0),
        ("Menu Classic", "Burger + frites + boisson", "Menus", "15.90", 850, False, 100),
    ]),
    ("Tokyo Bowl", "Cuisine japonaise et bowls frais.", "Livraison gratuite dès 30 € avec TOKYO30", "Japonais", "8 avenue de l'Opéra, Paris", "3.49", "15.00", 35, "4.8", [
        ("Chicken Teriyaki", "Poulet teriyaki, riz, légumes", "Bowls", "13.50", 650, False, 100),
        ("Salmon Bowl", "Saumon, avocat, riz vinaigré", "Bowls", "15.90", 590, False, 2),
        ("Gyozas", "6 gyozas au poulet", "Entrées", "6.90", 330, False, 0),
        ("Miso Soup", "Soupe miso traditionnelle", "Entrées", "3.20", 90, True, 100),
        ("Tofu Bowl", "Tofu grillé, riz et légumes", "Bowls", "12.90", 520, True, 100),
    ]),
    ("Green Kitchen", "Salades, wraps et options végétariennes.", "", "Healthy", "41 rue de Lyon, Paris", "1.99", "12.00", 20, "4.5", [
        ("Veggie Wrap", "Falafels, crudités, sauce tahini", "Wraps", "10.90", 480, True, 100),
        ("Chicken Caesar", "Poulet grillé, parmesan, salade", "Salades", "12.50", 560, False, 100),
        ("Quinoa Bowl", "Quinoa, légumes rôtis, avocat", "Bowls", "12.90", 510, True, 0),
        ("Fresh Juice", "Orange, pomme et gingembre", "Boissons", "4.50", 170, True, 100),
        ("Granola Bowl", "Yaourt, fruits et granola", "Desserts", "7.50", 390, True, 100),
    ]),
    ("Pizza Roma", "Pizzas romaines, pâtes et desserts italiens.", "", "Italien", "22 rue de la République, Paris", "2.49", "12.00", 30, "4.3", [
        ("Margherita", "Tomate, mozzarella, basilic", "Pizzas", "10.90", 760, True, 100),
        ("Regina", "Tomate, mozzarella, jambon, champignons", "Pizzas", "13.90", 840, False, 100),
        ("Quattro Formaggi", "Mozzarella, gorgonzola, parmesan, chèvre", "Pizzas", "14.50", 930, True, 0),
        ("Tiramisu", "Dessert italien au café", "Desserts", "6.50", 410, True, 100),
    ]),
    ("Couscous Atlas", "Cuisine marocaine familiale et généreuse.", "🎟️ Code ATLAS15 annoncé comme -15% sur ce restaurant", "Marocain", "7 boulevard Voltaire, Paris", "2.99", "25.00", 40, "4.9", [
        ("Couscous Royal", "Semoule, poulet, merguez et légumes", "Plats", "17.90", 980, False, 100),
        ("Tajine Poulet Citron", "Poulet, citron confit, olives", "Plats", "15.90", 760, False, 100),
        ("Tajine Légumes", "Légumes de saison, épices douces", "Plats", "13.90", 540, True, 0),
        ("Thé à la menthe", "Thé vert et menthe fraîche", "Boissons", "3.50", 40, True, 100),
    ]),
]

with app.app_context():
    db.drop_all()
    db.create_all()

    alice = User(name="Alice Martin", email="alice@example.com", role="customer", phone="0601020304")
    alice.set_password("Password123!")
    bob = User(name="Bob Dupont", email="bob@example.com", role="customer")
    bob.set_password("Password123!")
    admin = User(name="Admin QuickOrder", email="admin@quickorder.local", role="admin")
    admin.set_password("Admin123!")
    db.session.add_all([alice, bob, admin])
    db.session.flush()

    alice_address = Address(user_id=alice.id, label="Domicile", street="10 rue de Paris", postal_code="75001", city="Paris", instructions="Code 1234", is_default=True)
    bob_address = Address(user_id=bob.id, label="Bureau", street="25 avenue de France", postal_code="75013", city="Paris", is_default=True)
    db.session.add_all([alice_address, bob_address])

    restaurants = []
    for name, desc, promo, category, address, fee, minimum, time_min, rating, products in restaurants_data:
        r = Restaurant(name=name, description=desc, promo_text=promo, category=category, address=address,
                       delivery_fee=Decimal(fee), minimum_order=Decimal(minimum), delivery_time_min=time_min,
                       rating=Decimal(rating), is_open=True)
        db.session.add(r)
        db.session.flush()
        restaurants.append(r)
        for pname, pdesc, pcat, price, calories, veggie, stock in products:
            db.session.add(Product(restaurant_id=r.id, name=pname, description=pdesc, category=pcat,
                                   price=Decimal(price), calories=calories, is_vegetarian=veggie, stock=stock, available=True))

    closed = Restaurant(name="Night Sushi", description="Restaurant fermé — uniquement pour les tests QA.", promo_text="Fermé aujourd'hui", category="Japonais", address="5 rue des Tests, Paris", delivery_fee=Decimal("2.99"), minimum_order=Decimal("10.00"), delivery_time_min=45, rating=Decimal("3.8"), is_open=False)
    db.session.add(closed)
    db.session.flush()
    db.session.add_all([
        Product(restaurant_id=closed.id, name="Late Sushi Box", description="Produit d'un restaurant fermé.", category="Sushi", price=Decimal("14.00"), calories=600, is_vegetarian=False, stock=100, available=True),
        Product(restaurant_id=closed.id, name="Sushi épuisé", description="Produit fermé et hors stock.", category="Sushi", price=Decimal("12.00"), calories=500, is_vegetarian=False, stock=0, available=True),
    ])

    db.session.add_all([
        Coupon(code="WELCOME10", discount_percent=Decimal("10"), min_order_amount=Decimal("20"), max_discount=Decimal("8"), active=True, expires_at=datetime.utcnow() + timedelta(days=90)),
        Coupon(code="SAVE20", discount_percent=Decimal("20"), min_order_amount=Decimal("35"), max_discount=Decimal("12"), active=True, expires_at=datetime.utcnow() + timedelta(days=30)),
        Coupon(code="LUNCH5", discount_percent=Decimal("5"), min_order_amount=Decimal("10"), max_discount=Decimal("5"), active=True, expires_at=datetime.utcnow() + timedelta(days=365)),
        Coupon(code="TOKYO30", discount_percent=Decimal("100"), min_order_amount=Decimal("30"), max_discount=Decimal("3.49"), active=True, expires_at=datetime.utcnow() + timedelta(days=60)),
        Coupon(code="ATLAS15", discount_percent=Decimal("15"), min_order_amount=Decimal("20"), max_discount=Decimal("50"), active=True, expires_at=datetime.utcnow() + timedelta(days=60)),
        Coupon(code="EXPIRED10", discount_percent=Decimal("10"), min_order_amount=Decimal("0"), active=True, expires_at=datetime.utcnow() - timedelta(days=1)),
    ])
    db.session.flush()

    burger = restaurants[0]
    classic = Product.query.filter_by(restaurant_id=burger.id, name="Classic Burger").first()
    fries = Product.query.filter_by(restaurant_id=burger.id, name="Frites maison").first()
    order = Order(user_id=alice.id, address_id=alice_address.id, restaurant_id=burger.id, status="delivered",
                  subtotal=classic.price + fries.price, delivery_fee=burger.delivery_fee, discount=Decimal("0"),
                  total=classic.price + fries.price + burger.delivery_fee, payment_status="paid", payment_method="card",
                  payment_reference="PAY-DEMO001", customer_note="Sonner à l'arrivée")
    db.session.add(order)
    db.session.flush()
    db.session.add_all([
        OrderItem(order_id=order.id, product_id=classic.id, product_name=classic.name, unit_price=classic.price, quantity=1, line_total=classic.price),
        OrderItem(order_id=order.id, product_id=fries.id, product_name=fries.name, unit_price=fries.price, quantity=1, line_total=fries.price),
        Review(user_id=alice.id, restaurant_id=burger.id, order_id=order.id, rating=5, comment="Très bon burger et livraison rapide !"),
        Review(user_id=bob.id, restaurant_id=restaurants[1].id, rating=4, comment="Bowls frais, portion correcte."),
    ])
    db.session.commit()
    print("QuickOrder V3.1 database seeded successfully.")
    print("Demo customer: alice@example.com / Password123!")
    print("Demo customer: bob@example.com / Password123!")
    print("Demo admin: admin@quickorder.local / Admin123!")
    print("Swagger API key: quickorder-demo-key")
