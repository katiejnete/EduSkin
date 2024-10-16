# EduSkin
- A web application that allows users to better access data about cosmetic products. Built using Flask, with data scraped from [CosDNA](https://cosdna.com/) and [Google](https://www.google.com/).

## App Features
In response to the persistent challenges faced by consumers in navigating the complexities of skincare product selection, I have developed a comprehensive web application. Recognizing the prevalent struggle of individuals to access reliable information about cosmetic products, particularly when considering new additions to their skincare regimen, this platform aims to alleviate such uncertainties. Users get invaluable insights into product ingredients and crucial metrics. Empowering consumers with the ability to make informed decisions, our platform offers intuitive filters, enabling streamlined product exploration and selection.
- User can search for and sort through products based on:
  - number of reviews
  - price
  - rating
  - average acne score
  - average irritant score
  - average ingredient-safe score
- Users have access to product info pages with full list of ingredients and individual scores for each ingredient.
- Users can add liked products or products they want to try to their wishlist or favorites.
- Users receive skincare product recommendations based on their preferences, utilizing collaborative filtering to suggest items similar to those they favor. A content-based recommendation system suggests products liked by similar users, calculating similarity based on key attributes like rating, reviews, price, and scores. A matrix representation of users and products enables recommendation system creation. The k-Nearest Neighbors (KNN) algorithm identifies similar products to a given item. 
- Users can submit new products to be reviewed and processed before added to the database.

## Possible Future Implementation
- pagination
- star rating styling
- product barcode instead of product name
- better search functionality
