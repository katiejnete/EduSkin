from app import db, app
from csv import DictReader
from models import (
    User,
    Product,
    Ingredient,
    ProductIngredient,
    Wishlist,
    WishlistProduct,
)
import re
import csv
from random import sample, randint

NUM_USERS = 200
NUM_WISHLISTS = 100
NUM_WISHLIST_ITEMS = 1000
NUM_PRODUCTS = 1979

WISHLIST_CSV_HEADERS = ["user_id"]
WISH_PROD_CSV_HEADERS = ["wishlist_id", "product_id"]

with app.app_context():
    db.drop_all()
    db.create_all()

    with open("generator/user.csv", "r") as user:
        db.session.bulk_insert_mappings(User, DictReader(user))
        db.session.commit()

    with open("generator/ingredient.csv", "r") as ing:
        ing_reader = DictReader(ing)
        for row in ing_reader:
            name = row["name"]
            acne_score = row["acne_score"]
            irritant_score = row["irritant_score"]
            safety_score = row["safety_score"]
            acne_score = acne_score if acne_score else None            
            irritant_score = irritant_score if irritant_score else None            
            safety_score = safety_score if safety_score else None
            ingredient = Ingredient(name=name,acne_score=acne_score,irritant_score=irritant_score,safety_score=safety_score)
            db.session.add(ingredient)
        db.session.commit()

    with open("generator/product.csv", "r") as prod:
        prod_reader = DictReader(prod)
        for row in prod_reader:
            name = row["name"]
            timestamp = row["timestamp"]
            price = row["price"]
            rating = row["rating"]
            num_reviews = row["num_reviews"]
            image_url = row["image_url"]
            link = row["link"]
            avg_acne = row["avg_acne"]
            avg_irritant = row["avg_irritant"]
            avg_safety = row["avg_safety"]         
            price = price if price else None
            rating = rating if rating else None
            num_reviews = num_reviews if num_reviews else None
            image_url = image_url if image_url else None
            link = link if link else None
            avg_acne = avg_acne if avg_acne else None
            avg_safety = avg_safety if avg_safety else None
            avg_irritant = avg_irritant if avg_irritant else None
            product = Product(name=name,timestamp=timestamp,price=price,rating=rating,num_reviews=num_reviews,image_url=image_url,link=link,avg_acne=avg_acne,avg_irritant=avg_irritant,avg_safety=avg_safety)
            db.session.add(product)
        db.session.commit()    

    with open("generator/product_ingredient.csv", "r") as pi:
        db.session.bulk_insert_mappings(ProductIngredient, DictReader(pi))


    # use user uuid to create wishlist
    user_ids = db.session.execute(db.select(User.id)).scalars()
    user_ids = [user_id for user_id in user_ids]

    with open("generator/wishlist.csv", "w") as wishlist_csv:
        wishlist_writer = csv.DictWriter(wishlist_csv, fieldnames=WISHLIST_CSV_HEADERS)
        wishlist_writer.writeheader()
        user_set = set()
        for i in range(NUM_WISHLISTS):
            user_id = sample(user_ids, 1)[0]
            while user_id not in user_set:
                wishlist_writer.writerow(dict(user_id=user_id))
                user_set.add(user_id)

    with open("generator/wishlist.csv", "r") as wish:
        db.session.bulk_insert_mappings(Wishlist, DictReader(wish))
        db.session.commit()


    # use wishlist uuid to create wishlist product
    wish_ids = db.session.execute(db.select(Wishlist.id)).scalars()
    wish_ids = [wish_id for wish_id in wish_ids]

    with open("generator/wishlist_product.csv", "w") as wp:
        wp_writer = csv.DictWriter(wp, fieldnames=WISH_PROD_CSV_HEADERS)
        wp_writer.writeheader()
        for wish_id in wish_ids:
            prod_set = set()
            for i in range(randint(1, int(NUM_WISHLIST_ITEMS / NUM_WISHLISTS))):
                product_id = randint(1, NUM_PRODUCTS)
                while product_id not in prod_set:
                    wp_writer.writerow(dict(wishlist_id=wish_id, product_id=product_id))
                    prod_set.add(product_id)

    with open("generator/wishlist_product.csv", "r") as wp:
        db.session.bulk_insert_mappings(WishlistProduct, DictReader(wp))
        db.session.commit()
