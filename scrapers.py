from generator.create_csvs import (
    fill_data,
    scrape_google,
    scrape,
    scrape_ing,
    scrape_resource,
)
import time
import random

COS_URL = "https://cosdna.com"

def scrape_prod(name):
    name = name.replace(" ", "+")
    resource = f"/eng/product.php?radioSearch=1&q={name}&sort=date"
    soup = scrape(COS_URL, resource)
    results = soup.find("table", class_="w-full max-w-full")
    td = results.find("td", class_="py-2 border-b border-slate-300 px-0")
    link = td.find("a").attrs["href"]
    time.sleep(random.randint(1, 6))
    soup = scrape(COS_URL, link)
    results = soup.find_all("tr", class_="tr-i hover:bg-gray-100") 
    return results

def scrape_prod_ing(result):
    tds = result.find_all("td", class_="whitespace-nowrap")
    acne_score = tds[0].findChild("a").text.strip().strip("\n")
    irritant_score = tds[1].findChild("a").text.strip().strip("\n")
    safety_score = tds[2].findChild("a").text.strip().strip("\n")
    if acne_score and "-" in acne_score:
        idx = acne_score.index("-")
        acne_score = acne_score[idx + 1 :]
    elif acne_score:
        acne_score = acne_score
    else:
        acne_score = None  
    if irritant_score and "-" in irritant_score:
        idx = irritant_score.index("-")
        irritant_score = irritant_score[idx + 1 :]
    elif irritant_score:
        irritant_score = irritant_score
    else:
        irritant_score = None          
    if safety_score and "-" in safety_score:
        idx = safety_score.index("-")
        safety_score = safety_score[idx + 1 :]
    elif safety_score:
        safety_score = safety_score
    else:
        safety_score = None    
    return acne_score, irritant_score, safety_score