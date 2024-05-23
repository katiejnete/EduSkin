import csv
import requests
import time
from datetime import datetime
import random

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

p_r_csv_HEADERS = ["resource", "name"]
PRODUCT_CSV_HEADERS = [
    "name",
    "price",
    "timestamp",
    "rating",
    "num_reviews",
    "image_url",
    "link",
    "avg_acne",
    "avg_irritant",
    "avg_safety"
]
INGREDIENT_CSV_HEADERS = ["name", "acne_score", "irritant_score", "safety_score"]
PRODUCT_INGREDIENT_CSV_HEADERS = ["product_id", "ingredient_id"]

COS_URL = "https://cosdna.com"
G_URL = "https://www.google.com"
headers = {"User-Agent": "student use for educational purposes"}


def scrape(URL, RESRC):
    page = requests.get(f"{URL}{RESRC}", headers=headers)

    return BeautifulSoup(page.content, "html.parser")


# collect all resources on one page
def scrape_resource(RESRC):
    soup = scrape(COS_URL, RESRC)
    results = soup.find("table", class_="w-full max-w-full")
    tds = results.find_all("td", class_="py-2 border-b border-slate-300 px-0")
    resources = []
    for td in tds:
        product_link = td.find("a")
        href = product_link.attrs
        resources.append(href["href"])
    return resources


# collect all resource links for each type of skincare product: cleanser, serum, etc.
def collect_all_resources(name):
    resources = []
    for i in range(1, 13):
        resources = resources + scrape_resource(
            f"/eng/product.php?q={name}&sort=date&p={i}"
        )
        time.sleep(random.randint(1,6))
    return resources


# cleanser = collect_all_resources("cleanser")
# serum = collect_all_resources("serum")
# toner = collect_all_resources("toner")
# sunscreen = collect_all_resources("sunscreen")
# moisturizer = collect_all_resources("moisturizer")
# mask = collect_all_resources("mask")
# cream = collect_all_resources("cream")

# all_resources = cleanser + serum + toner + sunscreen + moisturizer + mask + cream

# r_set = set()
# with open("generator/prod_resource.csv","w") as file:
#     for r in all_resources:
#         if r not in r_set:
#             file.write(f"{r}\n")
#             r_set.add(r)   

# scrape ingredients data for each specific product
ing_set = set()
ing_dict = {}
ing_list = []
ing_id = 1


def scrape_ing(RESRC):
    global ing_id
    prod_ing = []
    soup = scrape(COS_URL, RESRC)
    results = soup.find_all("tr", class_="tr-i hover:bg-gray-100")
    for result in results:
        span = result.find("span", class_="colors")
        prod_ing.append(span.string)
        ingredient = {}
        if span.string not in ing_set:
            ing_set.add(span.string)
            ing_list.append(span.string)
            tds = result.find_all("td", class_="whitespace-nowrap")
            acne_score = tds[0].findChild("a").text.strip().strip("\n")
            ingredient["acne_score"] = acne_score
            irritant_score = tds[1].findChild("a").text.strip().strip("\n")
            ingredient["irritant_score"] = irritant_score
            safety_score = tds[2].findChild("a").text.strip().strip("\n")
            ingredient["safety_score"] = safety_score
            ingredient["id"] = ing_id
            if acne_score and "-" in acne_score:
                idx = acne_score.index("-")
                acne_score = int(acne_score[idx+1:])
            elif acne_score:
                acne_score = int(acne_score)
            else:
                acne_score = None
            if irritant_score and "-" in irritant_score:
                idx = irritant_score.index("-")
                irritant_score = int(irritant_score[idx+1:])
            elif irritant_score:
                irritant_score = int(irritant_score)
            else:
                irritant_score = None
            if safety_score and "-" in safety_score:
                idx = safety_score.index("-")
                safety_score = int(safety_score[idx+1:])
            elif safety_score:
                safety_score = int(safety_score)
            else:
                safety_score = None            
            ing_dict[f"{span.string}"] = ingredient
            ing_id += 1
        else:
            continue
    return prod_ing


# fill product data when amazon listing isn't found
def fill_data(product, soup):
    try:
        div = soup.find("div", class_="TXwUJf").text
        if "Missing: amazon" in div:
            product["price"] = soup.find("div", class_="fG8Fp uo4vr").find("span").text
            product["link"] = soup.find("div", class_="yuRUbf").find("a").attrs["href"]
            img_div = soup.find("div", class_="sX59Pb oLJ4Uc")
            product["image_url"] = img_div.find("img").attrs["src"]
        else:
            product["price"] = None
            product["link"] = None
            product["image_url"] = None
        product["rating"] = None
        product["num_reviews"] = None
        product["timestamp"] = datetime.now()
    except:
        product["price"] = None
        product["link"] = None
        product["rating"] = None
        product["num_reviews"] = None
        product["timestamp"] = datetime.now()
        product["image_url"] = None
    return product


# get product data from google
def scrape_google(query):
    product = {}
    product["name"] = query.lower()
    options = Options()
    options.add_argument("--headless=new")
    service = webdriver.ChromeService(executable_path="/Users/kate/eduskin/static/chromedriver")
    driver = webdriver.Chrome(options=options)
    RESRC = "/search?q=" + query.replace(" ", "+") + " amazon"
    val = f"{G_URL}{RESRC}"
    driver.get(val)
    for _ in range(1):
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, features="html.parser")
            div = soup.find("div", class_="MjjYud").text
            if "Missing:" in div:
                product = fill_data(product, soup)
                return product
            else:
                data = soup.find("div", class_="fG8Fp uo4vr")
                if not data:
                    driver.quit()
                    return
                spans = data.find_all("span")
                product["price"] = float(spans[4].text.strip("$"))
                product["timestamp"] = datetime.now()
                product["rating"] = float(spans[2].text.strip("Rating: "))
                product["num_reviews"] = int(spans[3].text.strip(" reviews").replace(",",""))
                product["link"] = (
                    soup.find("div", class_="yuRUbf").find("a").attrs["href"]
                )
                img_div = soup.find("div", class_="sX59Pb oLJ4Uc")
                product["image_url"] = img_div.find("img").attrs["src"]
        except:
            product = fill_data(product, soup)
            return product
    driver.quit()
    return product


def scrape_prod_name(RESRC):
    try:
        soup = scrape(COS_URL, RESRC)
        div = soup.find("div", class_="block-prodname").attrs["x-init"]
        start_idx = div.rfind("name")
        start_idx += 7
        end_idx = div.rfind('","no"')
        name = div[start_idx:end_idx]
        return name
    except:
        return False

# create ing csv 1
# with open("generator/ingredient.csv", "w") as ing_csv:
#     ing_writer = csv.DictWriter(ing_csv, fieldnames=INGREDIENT_CSV_HEADERS)
#     ing_writer.writeheader()
#     for i in ing_list:
#         ing = ing_dict.get(i)
#         ing_writer.writerow(
#             dict(
#                 name=i,
#                 acne_score=ing["acne_score"],
#                 irritant_score=ing["irritant_score"],
#                 safety_score=ing["safety_score"],
#             )
#         )
    
# new_dict = {}
# new_id = 1
# with open("generator/ingredient.csv","r") as ing:
#     ing_reader = csv.DictReader(ing)   
#     for row in ing_reader:
#         ingredient = {}
#         ingredient["id"] = new_id
#         ingredient["acne_score"] = row["acne_score"]
#         ingredient["irritant_score"] = row["irritant_score"]
#         ingredient["safety_score"] = row["safety_score"]
#         new_dict[row["name"]] = ingredient
#         new_id += 1
    
# create ing csv 2
# with open("generator/ingredient.csv", "r") as ing:
    # ing_reader = csv.DictReader(ing)
    # with open("generator/ing_new.csv","w") as ing_new:
    #     ing_writer = csv.DictWriter(ing_new, fieldnames=INGREDIENT_CSV_HEADERS)
    #     ing_writer.writeheader()    
    #     for row in ing_reader:
    #         name = row["name"]
    #         acne_score = row["acne_score"]
    #         irritant_score = row["irritant_score"]
    #         safety_score = row["safety_score"]
    #         if acne_score and "-" in acne_score:
    #             idx = acne_score.index("-")
    #             acne_score = int(acne_score[idx + 1 :])
    #         elif acne_score:
    #             acne_score = int(acne_score)
    #         else:
    #             acne_score = None
    #         if irritant_score and "-" in irritant_score:
    #             idx = irritant_score.index("-")
    #             irritant_score = int(irritant_score[idx + 1 :])
    #         elif irritant_score:
    #             irritant_score = int(irritant_score)
    #         else:
    #             irritant_score = None
    #         if safety_score and "-" in safety_score:
    #             idx = safety_score.index("-")
    #             safety_score = int(safety_score[idx + 1 :])
    #         elif safety_score:
    #             safety_score = int(safety_score)
    #         else:
    #             safety_score = None
    #         ing_writer.writerow(dict(
    #             name=name,
    #             acne_score=acne_score,
    #             irritant_score=irritant_score,
    #             safety_score=safety_score
    #         ))

# create product csv 1
# count = 1
# with open("generator/product_new.csv", "w") as product_csv:
#     product_writer = csv.DictWriter(product_csv, fieldnames=PRODUCT_CSV_HEADERS)
#     product_writer.writeheader()
#     with open("generator/product.csv", "r") as prod_orig:
#         product_reader = csv.DictReader(prod_orig)
#         for row in product_reader:
#             print(count)
#             try:
#                 if not row["price"]:
#                     product = scrape_google(row["name"])
#                     product_writer.writerow(
#                         dict(
#                             name=row["name"],
#                             price=product["price"],
#                             timestamp=product["timestamp"],
#                             rating=product["rating"],
#                             num_reviews=product["num_reviews"],
#                             image_url=product["image_url"],
#                             link=product["link"],
#                         )
#                     )
#                 else: 
#                     product_writer.writerow(dict(
#                             name=row["name"],
#                             price=row["price"],
#                             timestamp=row["timestamp"],
#                             rating=row["rating"],
#                             num_reviews=row["num_reviews"],
#                             image_url=row["image_url"],
#                             link=row["link"],                    
#                     ))
#             except:
#                 product_writer.writerow(dict(
#                         name=row["name"],
#                         price=row["price"],
#                         timestamp=row["timestamp"],
#                         rating=row["rating"],
#                         num_reviews=row["num_reviews"],
#                         image_url=row["image_url"],
#                         link=row["link"],                    
#                 ))                
#             time.sleep(random.randint(1, 6)) 
#             count += 1    

# create product csv 2
# import re
# with open("generator/product.csv", "r") as prod:
#     prod_reader = csv.DictReader(prod)
#     with open("generator/prod_new.csv","w") as prod_new:
#         prod_writer = csv.DictWriter(prod_new, fieldnames=PRODUCT_CSV_HEADERS)
#         prod_writer.writeheader()            
#         for row in prod_reader:
#             name = row["name"]
#             timestamp = row["timestamp"]
#             price = row["price"]

#             if " " in price:
#                 price = None
            # elif price == "":
            #     price = None
            # elif "$" in price:
            #     idx = price.index("$")
            #     price = float(price[idx + 1 :])
            # else:
            #     x = re.search(
            #         "([0-9][0-9][0-9]|[0-9]|[0-9][0-9]).([0-9][0-9]|[0-9])$", price
            #     )
            #     price = float(x[0])
            # rating = float(row["rating"].strip("Rating: ")) if row["rating"] else None
            # num_reviews = row["num_reviews"]
            # if " " in num_reviews:
            #     idx = num_reviews.index(" ")
            #     num_reviews = int(num_reviews[:idx].replace(",", ""))
            # elif num_reviews:
            #     num_reviews = num_reviews
            # else:
            #     num_reviews = None
            # image_url = row["image_url"] if row["image_url"] else None
            # link = row["link"] if row["link"] else None
            # avg_acne = float(row["avg_acne"]) if row["avg_acne"] else None
            # avg_irritant = float(row["avg_irritant"]) if row["avg_irritant"] else None
            # avg_safety = float(row["avg_safety"]) if row["avg_safety"] else None
            # prod_writer.writerow(dict(
            #     name=name,
            #     timestamp=timestamp,
            #     price=price,
            #     rating=rating,
            #     num_reviews=num_reviews,
            #     image_url=image_url,
            #     link=link,
            #     avg_acne=avg_acne,
            #     avg_irritant=avg_irritant,
            #     avg_safety=avg_safety
            # ))

#avg scores TURN 0 REVIEWS TO NONE
# pi_dict = {}
# ing_dict = {}
# ing_id = 1
# prod_id = 1
# with open("generator/ingredient.csv", "r") as ing:
#     ing_reader = csv.DictReader(ing)
#     for row in ing_reader:
#         ing_dict[ing_id] = row
#         ing_id += 1
# a_count = 0
# i_count = 0
# s_count = 0
# acne = 0
# irr = 0
# safety = 0
# with open("generator/product_ingredient.csv", "r") as pi:
#     pi_reader = csv.DictReader(pi)
#     for row in pi_reader:
#         if not pi_dict.get(row["product_id"]):
#             a_count = 0
#             i_count = 0
#             s_count = 0
#             acne = 0
#             irr = 0
#             safety = 0
#             ing_id = int(row["ingredient_id"])
#             # import pdb
#             # pdb.set_trace()
#             if not ing_dict[ing_id]["acne_score"]:
#                 continue
#             else:
#                 a_count+=1
#                 if "-" in ing_dict[ing_id]["acne_score"]:
#                     idx = ing_dict[ing_id]["acne_score"].index("-")
#                     acne += int(ing_dict[ing_id]["acne_score"][idx+1:])
#                 else:
#                     acne += int(ing_dict[ing_id]["acne_score"])
#             if not ing_dict[ing_id]["irritant_score"]:
#                 continue
#             else:
#                 i_count+=1
#                 if "-" in ing_dict[ing_id]["irritant_score"]:
#                     idx = ing_dict[ing_id]["irritant_score"].index("-")
#                     irr += int(ing_dict[ing_id]["irritant_score"][idx+1:])
#                 else:
#                     irr += int(ing_dict[ing_id]["irritant_score"])
#             safety = ing_dict[ing_id]["safety_score"]
#             if not safety:
#                 continue
#             else:
#                 s_count+=1
#                 if "-" in safety:
#                     idx = safety.index("-")
#                     safety = int(safety[idx+1:])
#                 else:
#                     safety = int(safety)
#             pi_dict[row["product_id"]] = {'acne_score': acne, 'irritant_score': irr, 'safety_score':safety}            
#         else:
#             ing_id = int(row["ingredient_id"])
#             if not ing_dict[ing_id]["acne_score"]:
#                 continue
#             else:
#                 a_count+=1
#                 if "-" in ing_dict[ing_id]["acne_score"]:
#                     idx = ing_dict[ing_id]["acne_score"].index("-")
#                     acne += int(ing_dict[ing_id]["acne_score"][idx+1:])
#                 else:
#                     acne += int(ing_dict[ing_id]["acne_score"])
#             if not ing_dict[ing_id]["irritant_score"]:
#                 continue
#             else:
#                 i_count+=1
#                 if "-" in ing_dict[ing_id]["irritant_score"]:
#                     idx = ing_dict[ing_id]["irritant_score"].index("-")
#                     irr += int(ing_dict[ing_id]["irritant_score"][idx+1:])
#                 else:
#                     irr += int(ing_dict[ing_id]["irritant_score"])
#             if not ing_dict[ing_id]["safety_score"]:
#                 continue
#             else:
#                 s_count+=1
#                 if "-" in ing_dict[ing_id]["safety_score"]:
#                     idx = ing_dict[ing_id]["safety_score"].index("-")
#                     safety += int(ing_dict[ing_id]["safety_score"][idx+1:])
#                 else:
#                     safety += int(ing_dict[ing_id]["safety_score"])
#             pi_dict[row["product_id"]] = {'acne_score': acne/a_count, 'irritant_score': irr/i_count, 'safety_score':safety/s_count}          
# prod_id = 1
# with open("generator/product.csv","r") as prod:
#     prod_reader = csv.DictReader(prod)
#     with open("generator/prod_new.csv","w") as prod_new:
#         prod_writer = csv.DictWriter(prod_new,fieldnames=PRODUCT_CSV_HEADERS)
#         prod_writer.writeheader()
#         for row in prod_reader:
#             try:
#                 if not row["num_reviews"]:
#                     row["num_reviews"] = 0
#                 prod_writer.writerow(dict(
#                     name=row["name"],
#                     price=row["price"],
#                     timestamp=row["timestamp"],
#                     rating=row["rating"],
#                     num_reviews=row["num_reviews"],
#                     image_url=row["image_url"],
#                     link=row["link"],
#                     avg_acne=pi_dict[str(prod_id)]["acne_score"],
#                     avg_irritant=pi_dict[str(prod_id)]["irritant_score"],
#                     avg_safety=pi_dict[str(prod_id)]["safety_score"]               
#                 ))
#                 prod_id += 1
#             except:
#                 prod_writer.writerow(dict(
#                     name=row["name"],
#                     price=row["price"],
#                     timestamp=row["timestamp"],
#                     rating=row["rating"],
#                     num_reviews=row["num_reviews"],
#                     image_url=row["image_url"],
#                     link=row["link"],
#                     avg_acne=None,
#                     avg_irritant=None,
#                     avg_safety=None               
#                 ))
#                 prod_id += 1                                

# create product ingredient csv 1
# prod_id = 1
# with open("generator/product_ingredient.csv", "w") as p_i_csv:
#     p_i_writer = csv.DictWriter(p_i_csv, fieldnames=PRODUCT_INGREDIENT_CSV_HEADERS)
#     p_i_writer.writeheader()
#     with open("generator/product.csv", "r") as prod:
#         prod_reader = csv.DictReader(prod)
#         for row in prod_reader:
#             try:
#                 print(prod_id)
#                 name = row["name"].replace(" ","+").encode('utf-8').decode('unicode-escape')
#                 resource = f"/eng/product.php?radioSearch=1&q={name}&sort=date"
#                 soup = scrape(COS_URL,resource)
#                 results = soup.find("table", class_="w-full max-w-full")
#                 td = results.find("td", class_="py-2 border-b border-slate-300 px-0")
#                 href = td.find("a").attrs["href"]
#                 time.sleep(random.randint(1, 6))
#                 prod_ing = scrape_ing(href)
#                 time.sleep(random.randint(1, 6))
#                 for ing in prod_ing:
#                     ing_id = ing_dict.get(ing)["id"]
#                     p_i_writer.writerow(dict(product_id=prod_id, ingredient_id=ing_id))
#                 prod_id += 1
#             except:
#                 p_i_writer.writerow(dict(product_id=prod_id, ingredient_id=0))
#                 prod_id += 1

# create product ingredient csv 2
# prod_dict = {}
# prod_id = 1
# with open("generator/product.csv","r") as prod:
#     prod_reader = csv.DictReader(prod)
#     for row in prod_reader:
#         prod_dict[prod_id] = row["name"]
#         prod_id += 1        
# with open("generator/product_ingredient.csv","r") as pi:
#     pi_reader = csv.DictReader(pi)
#     with open("generator/product_ingredient.csv","w") as pi_new:
#         pi_writer = csv.DictWriter(pi_new,fieldnames=PRODUCT_INGREDIENT_CSV_HEADERS)
#         pi_writer.writeheader()
#         for row in pi_reader:
#             if row["ingredient_id"] == '0':
#                 print(row["product_id"])
#                 name = prod_dict[int(row["product_id"])][:50].replace(" ","+")
#                 resource = f"/eng/product.php?radioSearch=1&q={name}&sort=date"
#                 soup = scrape(COS_URL,resource)
#                 results = soup.find("table", class_="w-full max-w-full")
#                 td = results.find("td", class_="py-2 border-b border-slate-300 px-0")
#                 link = td.find("a").attrs["href"]
#                 time.sleep(random.randint(1, 6))
#                 prod_ing = scrape_ing(link)
#                 for ing in prod_ing:
#                     try:
#                         add_ing = new_dict[ing]                             
#                         pi_writer.writerow(dict(
#                             product_id=row["product_id"],
#                             ingredient_id=add_ing["id"]
#                         ))
#                     except:
#                         ing = ing_dict[ing]
#                         with open("generator/ingredient.csv","a") as ing_csv:
#                             ing_writer = csv.DictWriter(ing_csv,fieldnames=INGREDIENT_CSV_HEADERS)
#                             ing_writer.writerow(dict(
#                                 name=ing,
#                                 acne_score=ing["acne_score"],
#                                 irritant_score=ing["irritant_score"],
#                                 safety_score=ing["safety_score"]
#                             ))
#                             pi_writer.writerow(dict(
#                                 product_id=prod_id,
#                                 ingredient_id=new_id
#                             ))
#                             prod_id += 1
#                             new_id += 1
#             else:
#                 pi_writer.writerow(dict(
#                     product_id=row["product_id"],
#                     ingredient_id=row["ingredient_id"]
#                 ))
            
