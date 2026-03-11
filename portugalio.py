import csv
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright


# -------------------------------
# USER INPUT
# -------------------------------

CATEGORY = "distribuicao"
LOCATION = "distrito-lisboa"

WAYBACK_DATE = "20230601000000"

BASE_URL = f"https://web.archive.org/web/{WAYBACK_DATE}/https://www.portugalio.com/{CATEGORY}/{LOCATION}/"

OUTPUT_FILE = "data/companies.csv"
TIMEMEOUT_MS = 10000

# Safety limits
MAX_PAGES = 2
MAX_RESULTS = 20


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

def scrape_page(page):

    companies = []

    # wait for companies to appear
    try:
        page.wait_for_selector("div.list-row", timeout=TIMEMEOUT_MS)

    except Exception as e:
        print("Page did not load results within 10 seconds. Aborting this page.")
        return companies

    rows = page.query_selector_all("div.list-row")

    for row in rows:

        try:

            # Name
            name_elmnt = row.query_selector("a.list-item-title")
            name = name_elmnt.inner_text().strip() if name_elmnt else "N/A"

            # Address
            address_elmnt = row.query_selector("span.list-item-address")
            address = address_elmnt.inner_text().strip() if address_elmnt else "N/A"

            # Postal Code
            postal_elmnt = row.query_selector("span.pc")
            postal_code = postal_elmnt.inner_text().strip() if postal_elmnt else "N/A"

            # Phones (None or multiple)
            phone_elmnt = row.query_selector_all(
                "span.list-item-phones-block"
            )

            phones = []

            for p in phone_elmnt:
                phones.append(p.inner_text().strip())

            phonelist = " | ".join(phones) if phones else "N/A"

            companies.append({
                "name": name,
                "address": address,
                "postal_code": postal_code,
                "phones": phonelist
            })
            print((f"Scraped: {name} # {address} # {postal_code} # {phonelist}"))
        except Exception as e:
            print("Error:", e)

    return companies


# -------------------------------
# NEXT PAGE
# -------------------------------

def next_page(page):

    next_button = page.query_selector("li.next a")

    if not next_button:
        return False

    next_button.click()

    time.sleep(random.uniform(2, 5)) #Plis no ban

    return True


# -------------------------------
# SAVE CSV
# -------------------------------

def save_csv(data, filename):
    namesplit = filename.rsplit('.', 1)
    savename = f"{namesplit[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{namesplit[1]}"
    with open(savename, "w", newline="", encoding="utf-8") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=["name", "address", "postal_code", "phones"]
        )

        writer.writeheader()
        writer.writerows(data)


# -------------------------------
# MAIN
# -------------------------------

def main():

    playwright, browser, page = setup_browser()

    page.goto(BASE_URL)

    time.sleep(random.uniform(3, 6))

    all_companies = []
    page_cnt = 0

    while True:

        print(f"Scraping page {page_cnt + 1}")

        page_data = scrape_page(page)

        all_companies.extend(page_data)

        page_cnt += 1

        print(f"Total companies: {len(all_companies)}")

        # limits
        if page_cnt >= MAX_PAGES:
            print("Reached max page limit")
            break

        if len(all_companies) >= MAX_RESULTS:
            print("Reached max results limit")
            break

        if not next_page(page):
            print("No more pages")
            break


    browser.close()
    playwright.stop()

    save_csv(all_companies, OUTPUT_FILE)

    print(f"Saved {len(all_companies)} companies")


if __name__ == "__main__":
    main()