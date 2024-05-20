from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import nulls_last
from sqlalchemy.sql import func

from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime
from queue import Queue
import threading

from scrapers import scrape_prod, scrape_prod_ing
from generator.create_csvs import scrape_google, scrape_resource

bcrypt = Bcrypt()
db = SQLAlchemy()
q = Queue(maxsize=0)

COS_URL = "https://cosdna.com"


class User(db.Model):

    __tablename__ = "users"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    username = db.Column(db.Text, nullable=False, unique=True)

    password = db.Column(db.Text, nullable=False)

    wishlist = db.relationship("Wishlist", cascade="all, delete", passive_deletes=True)

    @classmethod
    def signup(cls, username, password):
        hashed_pwd = bcrypt.generate_password_hash(password).decode("UTF-8")
        user = User(username=username, password=hashed_pwd)
        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def authenticate(cls, username, password):
        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user
            else:
                return False


class Product(db.Model):

    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String, nullable=False, unique=True)

    price = db.Column(db.Numeric)

    timestamp = db.Column(db.DateTime, default=datetime.now(), nullable=False)

    rating = db.Column(db.Numeric)

    num_reviews = db.Column(db.Integer)

    image_url = db.Column(db.Text, default="/static/images/product-default.png")

    link = db.Column(db.Text)

    avg_acne = db.Column(db.Numeric)

    avg_irritant = db.Column(db.Numeric)

    avg_safety = db.Column(db.Numeric)

    def add_prod_ing(self, name):
        results = scrape_prod(name)
        for result in results:
            span = result.find("span", class_="colors")
            try:
                ing = db.session.execute(
                    db.select(Ingredient).filter_by(name=span.string)
                ).one()[0]
            except:
                acne_score, irritant_score, safety_score = scrape_prod_ing(result)
                ing = Ingredient(
                    name=span.string,
                    acne_score=acne_score,
                    irritant_score=irritant_score,
                    safety_score=safety_score,
                )
                db.session.add(ing)
                db.session.commit()
            prod_ing = ProductIngredient(product_id=self.id, ingredient_id=ing.id)
            db.session.add(prod_ing)

    @classmethod
    def start_product_q(cls, app, name):
        q.put(name)
        while not q.empty():
            name = q.get()
            product = scrape_google(name)
            if not product:
                return
            prod = Product(
                name=product["name"],
                price=product["price"],
                timestamp=product["timestamp"],
                rating=product["rating"],
                num_reviews=product["num_reviews"],
                image_url=product["image_url"],
                link=product["link"],
            )
            with app.app_context():
                try:
                    name = name.replace(" ", "+")
                    resource = f"/eng/product.php?radioSearch=1&q={name}&sort=date"
                    scrape_resource(resource)
                except:
                    return
                db.session.add(prod)
                db.session.commit()
                prod.add_prod_ing(name)
                avg_acne, avg_irritant, avg_safety = db.session.query(
                    func.avg(Ingredient.acne_score).label("avg_acne"),
                    func.avg(Ingredient.irritant_score).label("avg_irritant"),
                    func.avg(Ingredient.safety_score).label("safety_score"),
                ).join(
                    ProductIngredient, ProductIngredient.ingredient_id == Ingredient.id
                ).filter(
                    ProductIngredient.product_id == prod.id
                ).all()[0]
                prod.avg_acne = avg_acne
                prod.avg_irritant = avg_irritant
                prod.avg_safety = avg_safety
                db.session.commit()

    @classmethod
    def add_product(cls, app, name):
        t = threading.Thread(
            target=cls.start_product_q,
            args=(
                app,
                name,
            ),
        )
        t.start()

    @classmethod
    def check_product(cls, name):
        try:
            db.session.execute(db.select(Product).filter_by(name=name)).scalar_one()
            db.session.execute(
                db.select(Product).filter(Product.name.ilike(f"{name}%"))
            )
            return True
        except:
            return False

    @classmethod
    def get_products(cls, search):
        products = db.session.execute(
            db.select(Product)
            .order_by(nulls_last(Product.num_reviews.desc()))
            .filter(Product.name.ilike(f"%{search}%"))
        ).scalars()
        products = [product for product in products]
        return products

    @classmethod
    def sort_products(cls, sort, search):
        match sort:
            case "popular":
                products = db.session.execute(
                    db.select(Product)
                    .order_by(nulls_last(Product.num_reviews.desc()))
                    .filter(Product.name.ilike(f"%{search}%"))
                ).scalars()
            case "price_lh":
                products = db.session.execute(
                    db.select(Product)
                    .order_by(Product.price, Product.price.asc())
                    .filter(Product.name.ilike(f"%{search}%"))
                ).scalars()
            case "price_hl":
                products = db.session.execute(
                    db.select(Product)
                    .order_by(nulls_last(Product.price.desc()))
                    .filter(Product.name.ilike(f"%{search}%"))
                ).scalars()
            case "rating":
                products = db.session.execute(
                    db.select(Product)
                    .order_by(nulls_last(Product.rating.desc()))
                    .filter(Product.name.ilike(f"%{search}%"))
                ).scalars()
            case "acne_score":
                products = db.session.execute(
                    db.select(Product)
                    .order_by(Product.avg_acne.asc())
                    .filter(Product.name.ilike(f"%{search}%"))
                ).scalars()
            case "irritant_score":
                products = db.session.execute(
                    db.select(Product)
                    .order_by(Product.avg_irritant.asc())
                    .filter(Product.name.ilike(f"%{search}%"))
                ).scalars()
            case "safety_score":
                products = db.session.execute(
                    db.select(Product)
                    .order_by(Product.avg_safety.asc())
                    .filter(Product.name.ilike(f"%{search}%"))
                ).scalars()
        products = [product for product in products]
        return products

    @classmethod
    def get_rec_products(cls, rec_ids):
        recs = []
        int_rec_ids = []
        for id in rec_ids:
            int_rec_id = int(id)
            product = db.get_or_404(Product, int(id))
            int_rec_ids.append(int_rec_id)
            recs.append(product)
        return recs, int_rec_ids

    @classmethod
    def sort_rec_products(cls, sort, int_rec_ids):
        products = []
        match sort:
            case "popular":
                products = db.session.execute(
                    db.select(Product)
                    .order_by(nulls_last(Product.num_reviews.desc()))
                    .filter(Product.id.in_(int_rec_ids))
                ).scalars()
            case "price_lh":
                products = db.session.execute(
                    db.select(Product)
                    .order_by(Product.price, Product.price.asc())
                    .filter(Product.id.in_(int_rec_ids))
                ).scalars()
            case "price_hl":
                products = db.session.execute(
                    db.select(Product)
                    .order_by(nulls_last(Product.price.desc()))
                    .filter(Product.id.in_(int_rec_ids))
                ).scalars()
            case "rating":
                products = db.session.execute(
                    db.select(Product)
                    .order_by(nulls_last(Product.rating.desc()))
                    .filter(Product.id.in_(int_rec_ids))
                ).scalars()
            case "acne_score":
                products = db.session.execute(
                    db.select(Product)
                    .order_by(Product.avg_acne.asc())
                    .filter(Product.id.in_(int_rec_ids))
                ).scalars()
            case "irritant_score":
                products = db.session.execute(
                    db.select(Product)
                    .order_by(Product.avg_irritant.asc())
                    .filter(Product.id.in_(int_rec_ids))
                ).scalars()
            case "safety_score":
                products = db.session.execute(
                    db.select(Product)
                    .order_by(Product.avg_safety.asc())
                    .filter(Product.id.in_(int_rec_ids))
                ).scalars()
        products = [product for product in products]
        return products


class Ingredient(db.Model):

    __tablename__ = "ingredient"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String, nullable=False, unique=True)

    acne_score = db.Column(db.Integer)

    irritant_score = db.Column(db.Integer)

    safety_score = db.Column(db.Integer)


class ProductIngredient(db.Model):

    __tablename__ = "product_ingredient"

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.Integer, db.ForeignKey("product.id", ondelete="CASCADE"), nullable=False
    )

    ingredient_id = db.Column(
        db.Integer, db.ForeignKey("ingredient.id", ondelete="CASCADE"), nullable=False
    )

    @classmethod
    def get_prod_ings(cls, product_id):
        ings = (
            db.session.query(Ingredient)
            .join(cls)
            .filter(cls.product_id == product_id)
            .all()
        )
        return ings


class Wishlist(db.Model):

    __tablename__ = "wishlist"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, default=uuid4
    )


class WishlistProduct(db.Model):

    __tablename__ = "wishlist_product"

    id = db.Column(db.Integer, primary_key=True)

    wishlist_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("wishlist.id", ondelete="CASCADE"),
        nullable=False, default=uuid4
    )

    product_id = db.Column(
        db.Integer, db.ForeignKey("product.id", ondelete="CASCADE"), nullable=False
    )

    @classmethod
    def get_favorites(cls, wishlist_id):
        """Get user's wishlist favorited products"""

        favorites = (
            db.session.query(Product)
            .join(cls)
            .filter(cls.wishlist_id == wishlist_id)
            .all()
        )
        return favorites

    @classmethod
    def remove_favorite(cls, user_id, product_id):
        """Remove product from user's wishlist."""

        fav_product = (
            db.session.query(cls)
            .join(Wishlist)
            .filter(Wishlist.user_id == user_id, cls.product_id == product_id)
            .one()
        )
        db.session.delete(fav_product)


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """
    db.app = app
    db.init_app(app)
