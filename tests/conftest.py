import pytest
from app import create_app
from app.extensions import db
from app.models import User, Restaurant, Product, Address


class TestConfig:
    TESTING = True
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
        user = User(name="Test User", email="test@example.com")
        user.set_password("Password123!")
        restaurant = Restaurant(name="Test Restaurant", description="Test", category="Test", address="Paris",
                                delivery_fee=2.99, minimum_order=0, delivery_time_min=20, rating=4.5)
        db.session.add_all([user, restaurant])
        db.session.flush()
        db.session.add(Product(restaurant_id=restaurant.id, name="Test Burger", description="Test", category="Burgers", price=10, stock=10))
        db.session.add(Address(user_id=user.id, label="Domicile", street="1 rue Test", postal_code="75001", city="Paris", is_default=True))
        db.session.add(Product(restaurant_id=restaurant.id, name="Rupture", description="Test", category="Burgers", price=10, stock=0))
        closed = Restaurant(name="Closed", description="Ferme", category="Test", address="Paris", is_open=False)
        db.session.add(closed)
        db.session.flush()
        db.session.add(Product(restaurant_id=closed.id, name="Closed Dish", description="Test", category="Test", price=10, stock=10))
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def logged(client):
    client.post("/login", data={"email": "test@example.com", "password": "Password123!"})
    return client
