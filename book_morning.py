from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime

# ══════════════════════════════════════════════════════════
YOUR_NAME      = "Abhi Love Devkota"
YOUR_EMAIL     = "abhilovedevkota@gmail.com"
YOUR_MATRICOLA = "548454"
FORM_URL       = "https://antonello.unime.it/prenotazione-postazione-biblioteca/?formid=28"
# ══════════════════════════════════════════════════════════

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.binary_location = "/usr/bin/google-chrome"
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def wait_for_element(driver, by, selector, timeout=30):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, selector))
    )

def select_furthest_date(driver):
    print("📅 Looking for available dates...")
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table.ui-datepicker-calendar"))
    )
    available_dates = driver.find_elements(
        By.CSS_SELECTOR,
        "td[data-handler='selectDay']:not(.ui-state-disabled) a[data-date]"
    )
    if not available_dates:
        raise Exception("❌ No available dates found!")
    furthest = max(available_dates, key=lambda x: int(x.get_attribute("data-date")))
    date_value = furthest.get_attribute("data-date")
    print(f"📅 Selecting date: {date_value}")
    driver.execute_script("arguments[0].click();", furthest)
    time.sleep(1.5)
    return date_value

def select_morning_slot(driver):
    print("⏰ Attempting morning slot...")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.slotsCalendarfieldname1_1"))
    )
    all_slots = driver.find_elements(
        By.CSS_SELECTOR,
        "div.slots [h1], div.slots a[h1]"
    )
    if not all_slots:
        raise Exception("❌ No time slots found!")
    print(f"🕐 Found {len(all_slots)} slot(s)")

    target_slot = all_slots[0]  # morning is always first slot

    seats = target_slot.find_elements(By.CSS_SELECTOR, "span.p")
    available = int(seats[0].text) if seats else 0
    print(f"💺 Available seats: {available}")

    if available == 0:
        raise Exception("❌ Morning slot is full!")

    driver.execute_script("arguments[0].click();", target_slot)
    time.sleep(1)
    print("✅ Morning slot selected")

def main():
    print("="*50)
    print("🚀 MORNING SLOT BOOKING")
    print("="*50)
    run_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    driver = get_driver()

    try:
        driver.get(FORM_URL)
        time.sleep(2)

        wait_for_element(driver, By.ID, "fieldname2_1").send_keys(YOUR_NAME)
        selected_date = select_furthest_date(driver)
        select_morning_slot(driver)

        wait_for_element(driver, By.ID, "email_1").send_keys(YOUR_EMAIL)
        wait_for_element(driver, By.ID, "fieldname5_1").send_keys(YOUR_MATRICOLA)

        cb1 = wait_for_element(driver, By.ID, "fieldname3_1")
        cb2 = wait_for_element(driver, By.ID, "fieldname6_1")
        if not cb1.is_selected():
            driver.execute_script("arguments[0].click();", cb1)
        if not cb2.is_selected():
            driver.execute_script("arguments[0].click();", cb2)
        time.sleep(0.5)

        submit_btn = wait_for_element(driver, By.CSS_SELECTOR, "div.pbSubmit")
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(3)

        page_text = driver.page_source.lower()
        success = any(w in page_text for w in ["grazie", "conferm", "thank", "success"])

        print("="*50)
        print(f"📊 RESULT — {run_time}")
        print("="*50)
        if success:
            print(f"🎉 SUCCESS! MORNING booked for {selected_date}!")
        else:
            print("⚠️ Submitted — confirmation unclear.")
        print("="*50)

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        driver.quit()
        print("🔒 Browser closed.")

main()
