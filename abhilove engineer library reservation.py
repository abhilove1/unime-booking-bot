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
YOUR_NAME      = "Bipana Bidari"
YOUR_EMAIL     = "bidaribipana9@gmail.com"
YOUR_MATRICOLA = "589082"
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

def select_time_slot(driver, slot_preference="evening"):
    print(f"⏰ Attempting {slot_preference} slot...")
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

    def get_available_seats(slot):
        seats = slot.find_elements(By.CSS_SELECTOR, "span.p")
        if not seats:
            print("⚠️ No availability counter — treating as FULL")
            return 0
        return int(seats[0].text)

    target_slot        = all_slots[-1] if slot_preference == "evening" else all_slots[0]
    actual_slot_booked = slot_preference
    available_seats    = get_available_seats(target_slot)
    print(f"💺 Available seats: {available_seats}")

    if available_seats == 0:
        if slot_preference == "evening":
            print("⚠️ Evening full! Falling back to morning...")
            target_slot        = all_slots[0]
            actual_slot_booked = "morning_fallback"
            morning_seats      = get_available_seats(target_slot)
            print(f"💺 Morning seats: {morning_seats}")
            if morning_seats == 0:
                raise Exception("❌ Both slots are full!")
        else:
            raise Exception("❌ Morning slot is full!")

    driver.execute_script("arguments[0].click();", target_slot)
    time.sleep(1)
    print(f"✅ Slot selected: {actual_slot_booked}")
    return actual_slot_booked

def fill_and_submit(driver, slot_preference="evening"):
    print(f"\n{'='*50}")
    print(f"🚀 Booking: {slot_preference.upper()} SLOT")
    print(f"{'='*50}")
    driver.get(FORM_URL)
    time.sleep(2)

    name_field = wait_for_element(driver, By.ID, "fieldname2_1")
    name_field.clear()
    name_field.send_keys(YOUR_NAME)

    selected_date = select_furthest_date(driver)
    actual_slot   = select_time_slot(driver, slot_preference)

    email_field = wait_for_element(driver, By.ID, "email_1")
    email_field.clear()
    email_field.send_keys(YOUR_EMAIL)

    mat_field = wait_for_element(driver, By.ID, "fieldname5_1")
    mat_field.clear()
    mat_field.send_keys(YOUR_MATRICOLA)

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
    success   = any(w in page_text for w in ["grazie", "conferm", "thank", "success"])
    if success:
        print(f"🎉 SUCCESS! {actual_slot.upper()} booked for {selected_date}!")
    else:
        print(f"⚠️ Submitted — confirmation unclear.")
    return success, actual_slot, selected_date

def main():
    driver   = get_driver()
    results  = {}
    run_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    try:
        # ── ROUND 1: Evening ──────────────────────────────
        success1, slot1, date1 = fill_and_submit(driver, "evening")
        results["round1"] = {"success": success1, "slot": slot1, "date": date1}

        time.sleep(5)

        # ── ROUND 2: Smart decision ───────────────────────
        if slot1 == "morning_fallback":
            print("ℹ️ Morning already booked as fallback — skipping Round 2.")
            results["round2"] = {"success": None, "slot": "skipped", "date": date1}
        else:
            success2, slot2, date2 = fill_and_submit(driver, "morning")
            results["round2"] = {"success": success2, "slot": slot2, "date": date2}

        # ── Summary ───────────────────────────────────────
        r1 = results["round1"]
        r2 = results["round2"]

        def status(r):
            if r["slot"] == "skipped": return "⏭️  Skipped"
            return "✅ Booked" if r["success"] else "❌ Failed"

        print(f"\n{'='*50}")
        print(f"📊 BOOKING SUMMARY — {run_time}")
        print(f"{'='*50}")
        print(f"Round 1 → {r1['slot'].upper():25s} {status(r1)}")
        print(f"Round 2 → {r2['slot'].upper():25s} {status(r2)}")
        print(f"{'='*50}")

    except Exception as e:
        print(f"\n❌ Error: {e}")

    finally:
        driver.quit()
        print("\n🔒 Browser closed.")

# ── RUN ───────────────────────────────────────────────────
main()
