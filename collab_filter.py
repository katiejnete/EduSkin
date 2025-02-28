from models import (
    User,
    Product,
    Wishlist,
    WishlistProduct,
    db,
)
import csv
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import os
from dotenv import load_dotenv
load_dotenv()

warnings.simplefilter(action="ignore", category=FutureWarning)

PRODUCT_CSV_HEADERS = ["id", "name"]
USER_CSV_HEADERS = ["id"]
FAVORITES_CSV_HEADERS = ["user_id", "wishlist_id", "product_id"]

from sqlalchemy import create_engine
engine = create_engine(os.environ.get(
        "DATABASE_URL", "postgresql:///eduskin"
    ))

def start_collab_filter():
    products = pd.read_sql("SELECT id, name FROM product", engine)
    favorites = pd.read_sql(
        "SELECT users.id as user_id, wishlist.id as wishlist_id, product.id as product_id FROM users JOIN wishlist ON wishlist.user_id = users.id JOIN wishlist_product ON wishlist_product.wishlist_id = wishlist.id JOIN product ON wishlist_product.product_id = product.id", engine)
    return products, favorites


from scipy.sparse import csr_matrix


def create_matrix(df):
    N = len(df["user_id"].unique())
    M = len(df["product_id"].unique())

    user_mapper = dict(zip(np.unique(df["user_id"]), list(range(N))))
    product_mapper = dict(zip(np.unique(df["product_id"]), list(range(M))))

    user_inv_mapper = dict(zip(list(range(N)), np.unique(df["user_id"])))
    product_inv_mapper = dict(zip(list(range(M)), np.unique(df["product_id"])))

    user_index = [user_mapper[i] for i in df["user_id"]]
    product_index = [product_mapper[i] for i in df["product_id"]]

    X = csr_matrix((df["product_id"], (product_index, user_index)), shape=(M, N))

    return X, product_mapper, product_inv_mapper


def get_collab_vals(products, favorites):
    user_freq = (
        favorites[["user_id", "product_id"]].groupby("user_id").count().reset_index()
    )
    user_freq.columns = ["user_id", "n_favorites"]

    mean_favorite = favorites.groupby("product_id")[["product_id"]].mean()

    lowest_favorited = mean_favorite["product_id"].idxmin()
    products.loc[products["id"] == lowest_favorited]

    highest_favorited = mean_favorite["product_id"].idxmax()
    products.loc[products["id"] == highest_favorited]

    favorites[favorites["product_id"] == highest_favorited]
    favorites[favorites["product_id"] == lowest_favorited]

    product_stats = favorites.groupby("product_id")[["product_id"]].agg(
        ["count", "mean"]
    )
    product_stats.columns = product_stats.columns.droplevel()

    X, product_mapper, product_inv_mapper = create_matrix(
        favorites
    )

    return X, product_mapper, product_inv_mapper


def find_similar_products(
    product_mapper,
    product_inv_mapper,
    product_id,
    X,
    k,
    metric="cosine",
    show_distance=False,
):

    neighbour_ids = []

    product_ind = product_mapper[product_id]
    product_vec = X[product_ind]
    k += 1
    kNN = NearestNeighbors(n_neighbors=k, algorithm="brute", metric=metric)
    kNN.fit(X)
    product_vec = product_vec.reshape(1, -1)
    neighbour = kNN.kneighbors(product_vec, return_distance=show_distance)
    for i in range(0, k):
        n = neighbour.item(i)
        neighbour_ids.append(product_inv_mapper[n])
    neighbour_ids.pop(0)
    return neighbour_ids


def recommend_products_for_user(
    favorites, products, product_mapper, product_inv_mapper, user_id, X, k=10
):
    pd_read = pd.read_sql(
    f"SELECT users.id as user_id, wishlist.id as wishlist_id, product.id as product_id FROM users JOIN wishlist ON wishlist.user_id = users.id JOIN wishlist_product ON wishlist_product.wishlist_id = wishlist.id JOIN product ON wishlist_product.product_id = product.id where user_id = '{user_id}'", engine)
    print(pd_read)
    df1 = favorites.query(f'user_id == "{user_id}"')
    # print(df1)
    if df1.empty:
        return

    product_id = df1[df1["product_id"] == max(df1["product_id"])]["product_id"].iloc[0]

    product_names = dict(zip(products["id"], products["name"]))

    similar_ids = find_similar_products(
        product_mapper, product_inv_mapper, product_id, X, k
    )
    product_name = product_names.get(product_id, "Product not found")

    if product_name == "Product not found":
        return

    return similar_ids
