import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def scrape_zus_outlets():
    url = "https://zuscoffee.com/category/store/kuala-lumpur-selangor/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'lxml')

    outlets = []

    # Find all outlet blocks (adjust selector)
    outlet_blocks = soup.select('div.store-item')  # Example — adjust as needed

    for block in outlet_blocks:
        name = block.select_one('h3.store-name').get_text(strip=True) if block.select_one('h3.store-name') else "Unknown Outlet"
        address = block.select_one('p.address').get_text(strip=True) if block.select_one('p.address') else ""
        hours = block.select_one('p.hours').get_text(strip=True) if block.select_one('p.hours') else ""
        services = ", ".join([s.get_text(strip=True) for s in block.select('ul.services li')]) if block.select('ul.services li') else ""

        outlets.append({
            "name": name,
            "address": address,
            "opening_hours": hours,
            "services": services
        })

    df = pd.DataFrame(outlets)
    df.to_csv("data/outlets.csv", index=False)
    print(f"Scraped {len(outlets)} outlets to data/outlets.csv")

if __name__ == "__main__":
    scrape_zus_outlets()