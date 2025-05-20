import os
import sqlite3
import time
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load login credentials from .env
load_dotenv()
EMAIL = "selgrably@diversified-metals.ca"
PASSWORD = "ZacDiver2025!"

LOGIN_URL = "https://app.portpro.io/login"
DB_PATH = 'databases/Run Sheet Database.db'

def scrape_and_save():
    options = Options()
    options.add_argument("--window-size=1920,1080")
    # Uncomment to see browser during testing:
    options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(LOGIN_URL)
        wait = WebDriverWait(driver, 30)

        # Login flow
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]'))).send_keys(EMAIL)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]'))).send_keys(PASSWORD)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))).click()
        print("✅ Submitted login form")

        time.sleep(5)

        # Confirm login
        if "login" in driver.current_url.lower():
            print("❌ Login failed or redirected to login page.")
            return
        print("✅ Logged in. Page title:", driver.title)

        # Wait for table
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(3)

        # Extract header map
        header_map = {}
        headers = driver.find_elements(By.CSS_SELECTOR, "thead th")
        for i, th in enumerate(headers):
            key = th.text.strip().lower()
            if key:
                header_map[key] = i

        print("📌 Header Map:", header_map)

        required_keys = [
            "load status",
            "container #",
            "purchase order #",
            "container eta",
            "last free day",
            "per diem free day"
        ]

        for k in required_keys:
            if k not in header_map:
                raise Exception(f"Missing expected column: {k}")

        # Parse rows
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        if not rows:
            print("❌ No rows found.")
            return

        container_data = []
        for row in rows:
            cols = row.find_elements(By.CSS_SELECTOR, "td")
            if len(cols) < len(header_map):
                continue

            container_data.append({
                "status": cols[header_map["load status"]].text.strip(),
                "container_number": cols[header_map["container #"]].text.strip(),
                "po_number": cols[header_map["purchase order #"]].text.strip(),
                "eta": cols[header_map["container eta"]].text.strip(),
                "last_free_day": cols[header_map["last free day"]].text.strip(),
                "per_diem_day": cols[header_map["per diem free day"]].text.strip(),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        print(f"✅ Found {len(container_data)} containers.")

        # Save to database
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM incoming_containers")

        for c in container_data:
            cur.execute("""
                INSERT INTO incoming_containers (
                    status, container_number, po_number, eta, last_free_day, per_diem_day, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                c["status"], c["container_number"], c["po_number"],
                c["eta"], c["last_free_day"], c["per_diem_day"], c["last_updated"]
            ))

        conn.commit()
        conn.close()
        print("✅ Data saved to database.")

    except Exception as e:
        print("❌ Error scraping containers:", e)

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_and_save()
