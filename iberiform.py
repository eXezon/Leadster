import csv
import json
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright


# -------------------------------
# USER INPUT
# -------------------------------

#COMPANY_ID = 32006224

URLS = [32006224]
BASE_URL = "https://www.iberinform.pt/empresa/{}"

OUTPUT_FILE = "data/companies.csv"
TIMEMEOUT_MS = 10000

# -------------------------------
# BROWSER SETUP
# -------------------------------

def setup_browser():

    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(
        headless=False,
        slow_mo=300 # slow down actions to avoid being blocked - CAN BE REMOVED FOR FASTER SCRAPING - Copilot comment ¯\_(ツ)_/¯
    )

    page = browser.new_page()

    return playwright, browser, page


# -------------------------------
# SCRAPE RESULTS FROM PAGE
# -------------------------------

def scrape_page(page, url):
    
    company = {
        "name": "N/A",
        "url": "N/A",
        "nif": "N/A",
        "address": "N/A",
        "postal_code": "N/A",
    }

    time.sleep(random.uniform(3, 6))
    
    try:
        page.goto(url)

        # wait for json structured data
        page.wait_for_selector('div.col-md-6.flex-cont.container-left > script[type^="application/ld+json"]', timeout=TIMEMEOUT_MS,state='attached')

    except Exception as e:
        print(f"Page did not load results within {TIMEMEOUT_MS/1000} seconds. Aborting this page.")
        return company
    
    try:
        
        json_text = page.locator('script[type="application/ld+json"]').first.inner_text()
        data = json.loads(json_text)

        
        #First-level
        main_elemnt = data.get("mainEntity", {})
        #Second-level (Address,Postal Code)
        address = main_elemnt.get("address", {})
        
        company["name"] = main_elemnt.get("name", "N/A")
        company["url"] = main_elemnt.get("url", "N/A")
        company["nif"] = main_elemnt.get("taxID", "N/A")
        company["address"] = address.get("streetAddress", "N/A")
        company["postal_code"] = address.get("postalCode", "N/A")
        
        print((f"Scraped: {company['name']} # {company['url']} # {company['nif']} # {company['address']} # {company['postal_code']}"))
        
    except Exception as e:
        print("Error parsing JSON data:", e)
        

    return company



def save_to_csv(data, filename):

    name_split = filename.rsplit('.', 1)
    savename = f"{name_split[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{name_split[1]}"
    with open(savename, "w", newline="", encoding="utf-8") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=["name","url","nif","address","postal_code"],
        )

        writer.writeheader()
        writer.writerows(data)



def main():

    playwright, browser, page = setup_browser()

    all_companies = []

    for company_id in URLS:
        
        url = BASE_URL.format(company_id)

        print(f"Scraping {url}")

        data = scrape_page(page, url)

        if data:
            all_companies.append(data)

    browser.close()
    playwright.stop()

    save_to_csv(all_companies, OUTPUT_FILE)

    print(f"Saved company")

if __name__ == "__main__":
    main()