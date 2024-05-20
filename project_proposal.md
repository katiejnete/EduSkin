# Project Proposal

|            | Description                                                                                                                                                                                                                                                                                                                                              | Fill in                                                                                                                      |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Tech Stack | What tech stack will you use for your final project? It is recommended to use the following technologies in this project: Python/Flask, PostgreSQL, SQLAlchemy, Heroku, Jinja, RESTful APIs, JavaScript, HTML, CSS. Depending on your idea, you might end up using WTForms and other technologies discussed in the course.                               | python/flask, psql, jinja, js, html, css                                                                                     |
| Type       | Will this be a website? A mobile app? Something else?                                                                                                                                                                                                                                                                                                    | web app                                                                                                                      |
| Goal       | What goal will your project be designed to achieve?                                                                                                                                                                                                                                                                                                      | make skincare information more accessible and feasible                                                                       |
| Users      | What kind of users will visit your app? In other words, what is the demographic of your users?                                                                                                                                                                                                                                                           | skincare enthusiasts or teens, adults, and seniors with skin issues                                                          |
| Data       | What data do you plan on using? How are you planning on collecting your data? You may have not picked your actual API yet, which is fine, just outline what kind of data you would like it to contain. You are welcome to create your own API and populate it with data. If you are using a Python/Flask stack, you are required to create your own API. | using cosmetic product ingredients data, plan on scraping data from cosdna.com, acne score, irritant score, and safety score |

# Breakdown

- Determining the database schema
  - User (uuid, username, password)
  - Skincare Product (id, name, price, timestamp, rating from google, image url, google link)
  - Cosmetic Ingredient (id, cosmetic ingredient, acne score, irritant score, safety score)
  - ProductIngredient(id, product id, ingredient id)
  - Wishlist (uuid, user id)
  - WishlistProduct (id, wishlist id, product id)
- Sourcing your data
  - Scrape from cosdna.com
    - cosmetic ingredients data
      - acne score
      - irritant score
      - safety score
      - reviews?
  - Scrape from google search results
    - rating
    - add everything on excel sheet and use script to extract values
- Determining user flow(s)
    - makes it easy to find product data when searching for product
    - find and sort products based on rating, price, score, bestseller
    - wishlist
    - get recommended products based on wishlist
    - add product?
- Setting up the backend and database
- Setting up the frontend
  - navbar
    - Home
    - Search
    - Get recommended skincare
    - User
    - wishlist?
  - Home
    - div Good skin days start here: Personalized and accessible skincare at your fingertips
    - div Common skin issues
    - div Easily find products with acne safe, irritant safe, ingredient safe icons
    - div ratings and budget friendly?
  - Search
    - product: image, link, name, rating, popularity, acne safe/irritant safe/ingredient safe icon
  - Product Page
    - ingredients list with scores
    - rating + num of reviews
    - image
    - name
    - price
    - google link
  - User page
    - current user details
    - edit skin details page
  - Recommended
    - Safe for user's skin issues at different price points
  - Login/signup
  - If time: Wishlist
- What functionality will your app include?
  - search
  - recommended skincare
  - wishlist?
