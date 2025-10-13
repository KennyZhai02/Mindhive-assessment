import requests
from bs4 import BeautifulSoup
import json
import os

def scrape_zus_drinkware():
    url = "https://shop.zuscoffee.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'lxml')

    products = []
    # Find all product cards (adjust selector based on actual HTML)
    product_cards = soup.select('div.product-item')  # Example — adjust as needed

    for card in product_cards:
        title = card.select_one('h3.product-title').get_text(strip=True) if card.select_one('h3.product-title') else "Unknown Product"
        price = card.select_one('span.price').get_text(strip=True) if card.select_one('span.price') else "N/A"
        desc = card.select_one('p.product-desc').get_text(strip=True) if card.select_one('p.product-desc') else ""

        products.append({
            "title": title,
            "price": price,
            "description": desc,
            "url": url  # You can extract actual product URL if available
        })

    # Save to JSONL for ingestion
    os.makedirs("data", exist_ok=True)
    with open("data/drinkware.jsonl", "w") as f:
        for p in products:
            f.write(json.dumps(p) + "\n")

    print(f"Scraped {len(products)} products.")

if __name__ == "__main__":
    scrape_zus_drinkware()