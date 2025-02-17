import os

from flask import Flask, render_template, request, flash, redirect, session, g
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv

from models import (
    db,
    connect_db,
    User,
    Product,
    ProductIngredient,
    Wishlist,
    WishlistProduct,
)
from forms import UserAddForm, LoginForm, ProductForm, SortForm

import pandas as pd
from collab_filter import (
    start_collab_filter,
    get_collab_vals,
    recommend_products_for_user as recommend,
)

load_dotenv(".env")

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.config["DEBUG"] = False

with app.app_context():
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:9XmZes5RBPs1GnoV@db.ydxaxaxubaylcfwudqan.supabase.co:5432/postgres"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ECHO"] = False
    app.config["SECRET_KEY"] = os.getenv("API_KEY")
    connect_db(app)


@app.before_request
def add_user_to_g():

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route("/signup", methods=["GET", "POST"])
def signup():

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(username=form.username.data, password=form.password.data)
            wishlist = Wishlist(user_id=user.id)
            db.session.add(wishlist)
            db.session.commit()
        except IntegrityError as e:
            if "(username)" in e.args[0]:
                flash("Username already taken", "danger")
                return render_template("user/signup.html", form=form)

        do_login(user)
        flash(f"Welcome, {user.username}!", "success")
        return redirect("/")

    else:
        return render_template("user/signup.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")
        flash("Invalid credentials.", "danger")

    return render_template("user/login.html", form=form)


@app.route("/logout")
def logout():
    """Handle logout of user."""

    do_logout()

    return redirect("/")


##############################################################################
# Product pages


@app.route("/product/new", methods=["GET", "POST"])
def product_add():
    """Add product:
    Show form if GET. If valid, update and redirect to product page."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = ProductForm()

    if form.validate_on_submit():
        name = form.name.data.lower()
        check = Product.check_product(name)
        if check:
            flash(
                "Product already exists in EduSkin. Please try a different one.", "info"
            )
            return redirect("/")
        else:
            Product.add_product(app, name)
            flash(
                "Your request has been received! Give us a moment to review and process submitted product.",
                "info",
            )
            return redirect("/")

    return render_template("product/new.html", form=form)


@app.route("/product", methods=["GET", "POST"])
def show_products():
    """Page list products matching search, takes q param in querystring to search by product name"""

    search = request.args.get("q")

    if not search:
        return redirect("/")

    form = SortForm()

    products = Product.get_products(search)
    if not products:
        flash("Sorry, no products were found", "danger")

    if form.validate_on_submit():
        sort = form.sort.data
        products = Product.sort_products(sort, search)
        if not products:
            flash("Sorry, no products were found", "danger")

    if not g.user:
        favorites = None
    else:
        favorites = WishlistProduct.get_favorites(g.user.wishlist[0].id)

    return render_template(
        "product/index.html",
        products=products,
        favorites=favorites,
        search=search,
        form=form,
    )


@app.route("/product/acne-safe", methods=["GET", "POST"])
def show_acne_safe():
    search = ""
    products = Product.sort_products("acne_score", search)
    if not g.user:
        favorites = None
    else:
        favorites = WishlistProduct.get_favorites(g.user.wishlist[0].id)
    form = SortForm()
    product_ids = []
    for prod in products:
        product_ids.append(prod.id)
    if form.validate_on_submit():
        sort = form.sort.data
        products = Product.sort_rec_products(sort, product_ids)
        return render_template(
            "product/acne-safe.html", products=products, form=form, favorites=favorites
        )
    return render_template(
        "product/acne-safe.html", products=products, form=form, favorites=favorites
    )


@app.route("/product/anti-aging", methods=["GET", "POST"])
def show_anti_aging():
    search = "sunscreen"
    products = Product.get_products(search)
    if not g.user:
        favorites = None
    else:
        favorites = WishlistProduct.get_favorites(g.user.wishlist[0].id)
    form = SortForm()
    product_ids = []
    for prod in products:
        product_ids.append(prod.id)
    if form.validate_on_submit():
        sort = form.sort.data
        products = Product.sort_rec_products(sort, product_ids)
        return render_template(
            "product/anti-aging.html", products=products, form=form, favorites=favorites
        )
    return render_template(
        "product/anti-aging.html", products=products, form=form, favorites=favorites
    )


@app.route("/product/<int:product_id>")
def show_product(product_id):
    """Show product page."""

    product = db.get_or_404(Product, product_id)
    ings = ProductIngredient.get_prod_ings(product_id)
    if not g.user:
        favorites = None
    else:
        favorites = WishlistProduct.get_favorites(g.user.wishlist[0].id)
    return render_template(
        "product/show.html", product=product, ings=ings, favorites=favorites
    )


@app.route("/product/recommended", methods=["GET", "POST"])
def show_recommended_products():
    """Show recommended products based on user's favorites."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    products, favorites = start_collab_filter()
    X, product_mapper, product_inv_mapper = get_collab_vals(products, favorites)
    rec_ids = recommend(
        favorites, products, product_mapper, product_inv_mapper, g.user.id, X, k=10
    )
    if rec_ids:
        recs, int_rec_ids = Product.get_rec_products(rec_ids)
        form = SortForm()
        favorites = WishlistProduct.get_favorites(g.user.wishlist[0].id)
        if form.validate_on_submit():
            sort = form.sort.data
            products = Product.sort_rec_products(sort, int_rec_ids)
            return render_template(
                "product/recommended.html",
                products=products,
                form=form,
                favorites=favorites,
            )
        else:
            return render_template(
                "product/recommended.html",
                products=recs,
                form=form,
                favorites=favorites,
            )
    else:
        return redirect("/wishlist")


##############################################################################
# Wishlist pages


@app.route("/wishlist")
def show_wishlist():
    """Show only user's wishlist page."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    wishlist = g.user.wishlist[0]
    favorites = WishlistProduct.get_favorites(wishlist.id)

    if not favorites:
        flash("Please add favorites to view this page.", "info")
    return render_template("wishlist/show.html", favorites=favorites)


@app.route("/wishlist/add/<int:product_id>", methods=["POST"])
def add_product_to_wishlist(product_id):
    """Add product to wishlist for currently logged in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    fav_product = db.get_or_404(Product, product_id)

    favorites = WishlistProduct.get_favorites(g.user.wishlist[0].id)

    if fav_product in favorites:
        WishlistProduct.remove_favorite(g.user.id, fav_product.id)
        db.session.commit()
    else:
        wish_prod = WishlistProduct(
            wishlist_id=g.user.wishlist[0].id, product_id=product_id
        )
        db.session.add(wish_prod)
        db.session.commit()

    return redirect(request.referrer)


##############################################################################
# Homepage and error pages


@app.route("/")
def homepage():
    if g.user:
        return render_template("home.html")
    else:
        return render_template("home.html")


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")


##############################################################################
# Turn off all caching in Flask


@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers["Cache-Control"] = "public, max-age=0"
    return req
