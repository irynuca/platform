from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import sqlite3
import time
import os
import re
from datetime import datetime
from urllib.parse import urljoin


#===== TO DO ======
#de fixat faptul ca inca mai apare "macro" la category acolo exista ticker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Path to app/ directory
DATA_DIR = os.path.join(BASE_DIR, "data")  # Path to data/
DB_PATH = os.path.join(DATA_DIR, "financials.db")  # Full path to database
INSSE_BASE_URL = "https://insse.ro"

# Define the BET Index Ticker List
BET_INDEX_TICKERS = [
    "AAG", "ALR", "ALT", "ALU", "AQ", "AROBS", "ARS", "ARTE", "ARM", "ATB", "BCM", "BIO", "BNET", "BRD", "BRK", "BVB", "CAOR", 
    "CBC", "CMF", "CMP", "COMI", "COTE", "CRC", "DIGI", "EBS", "ECT", "EFO", "EL", "ELJ", "EVER", "FP", "GREEN", "H2O", "IARV", 
    "IMP", "INFINITY", "LION", "LONG", "M", "MCAB", "MECE","OIL", "ONE", "PBK", "PE", "PPL", "PREB", "PTR", "RMAH", "ROC1", "ROCE", 
    "RPH", "RRC", "SAFE", "SFG", "SMTL", "SNG", "SNN", "SNO", "SNP", "SOCP", "STZ", "TBK", "TBM", "TEL", "TGN", "TLV", 
    "TRANSI", "TRP", "TTS", "TUFE", "VNC", "WINE", "BRM", "CMCM", "CNTE", "ELGS", "ELMA", "ENP", "NAPO", "PREH",
    "STK", "UAM", "UCM"]

def clear_old_events():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM financial_events")
        conn.commit()
        print("Cleared old events from financial_events table.")
    except sqlite3.Error as e:
        print(f"Database Error while clearing old events: {e}")
    finally:
        conn.close()

def parse_romania_date(date_string):
    try:
        # Handle BNR date format: "02.05.2025"
        if re.match(r"\d{2}\.\d{2}\.\d{4}", date_string):
            return datetime.strptime(date_string, "%d.%m.%Y").strftime("%Y-%m-%d")
        
        # Handle Romanian month format
        clean_date = re.search(r"\d{1,2}\s+[A-Za-zăîâșț]+\s+\d{4}", date_string)
        if clean_date:
            parts = clean_date.group().strip().lower().split()
            day = parts[0].zfill(2)
            month_ro = parts[1]
            year = parts[2]
            MONTH_MAP_RO = {
                "ianuarie": "01", "februarie": "02", "martie": "03",
                "aprilie": "04", "mai": "05", "iunie": "06",
                "iulie": "07", "august": "08", "septembrie": "09",
                "octombrie": "10", "noiembrie": "11", "decembrie": "12"
            }
            month = MONTH_MAP_RO.get(month_ro)
            if not month:
                print(f"⚠️ Unknown month: {month_ro}")
                return None
            return f"{year}-{month}-{day}"
        
        # Fallback for unrecognized formats
        print(f"⚠️ Unexpected date format: {date_string}")
        return None

    except Exception as e:
        print(f"⚠️ Failed to parse date: {date_string} ({e})")
        return None

def parse_period_reference(title):
    period_patterns = [
        (r"(?i)semestriale\s*(\d{4})", "6M"),
        (r"(?i)semestrul\s*[I1]\s*(\d{4})", "6M"),
        (r"(?i)trimestrul\s*[I1]\s*(\d{4})", "3M"),
        (r"(?i)trimestrul\s*[III3]\s*(\d{4})", "9M")
    ]
    for pattern, period_type in period_patterns:
        match = re.search(pattern, title)
        if match:
            year = match.group(1)
            if period_type == "3M":
                return f"3M/{year[-2:]}", f"{year}-01-01", f"{year}-03-31"
            elif period_type == "6M":
                return f"6M/{year[-2:]}", f"{year}-01-01", f"{year}-06-30"
            elif period_type == "9M":
                return f"9M/{year[-2:]}", f"{year}-01-01", f"{year}-09-30"
    return None, None, None

def scrape_bvb():
    events = []
    driver=webdriver.Chrome()

    try:
        driver.get("https://bvb.ro/FinancialInstruments/SelectedData/FinancialCalendar")
        time.sleep(5)
        segment_button = driver.find_element(By.ID, "lb1")
        segment_button.click()
        time.sleep(3)

        while True:
            # Get the current page source
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            events_table = soup.find("table", class_="table table-hover dataTable no-footer generic-table compact")
            
            if not events_table:
                print("❌ No events table found.")
                break

            rows = events_table.find_all("tr", class_=["odd", "even"])

            for row in rows:
                date_div = row.find("div", class_="evDate")
                date_raw = date_div.text.strip() if date_div else "Unknown"
                event_date = parse_romania_date(date_raw)

                ticker_b = row.find("b")
                ticker = ticker_b.text.strip() if ticker_b else "Unknown"

                event_p = row.find("p")
                event_name = event_p.text.strip() if event_p else "Unknown"

                print(f"📅 Extracted Event: Ticker={ticker}, Date={event_date}, Title={event_name}")
                events.append({
                    "Ticker": ticker,
                    "Date": event_date,
                    "Event name": event_name
                })

            # Check for the next page button
            try:
                next_button = driver.find_element(By.ID, "gv_next")
                if "disabled" in next_button.get_attribute("class"):
                    print("🛑 Reached the last page. No more events to scrape.")
                    break
                else:
                    # Scroll to the next button and click
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    next_button.click()
                    print("➡️ Moving to the next page...")
                    
                    # Use a more responsive wait
                    time.sleep(3)  # Reduce the wait time to improve responsiveness
            except Exception as e:
                print(f"⚠️ Failed to go to the next page: {e}")
                break
    except Exception as e:
        print(f"❌ Scraping error: {e}")
    finally:
        driver.quit()
        print("🚀 BVB Scraping complete. Browser closed.")

    return events  


def process_and_insert_bvb_events(bvb_events):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for event in bvb_events:
            ticker = event.get("Ticker")
            event_date = event.get("Date")
            title = event.get("Event name")
            description = title

            # Correct category logic
            category = "company" if ticker in BET_INDEX_TICKERS else "macro"
            normalized_title = re.sub(r"\s+", " ", title.lower().strip())

            # Improved event type detection
            if re.search(r"teleconferin(ț|t)a|înt(â|a)lnire cu anali(ș|s)ti", normalized_title):
                event_type = "earnings_conf_call"
            elif re.search(r"ex-data dividend", normalized_title):
                event_type = "ex_date"
            elif re.search(r"aga ordinar(ă|a) anual(ă|a)", normalized_title):
                event_type = "annual_ogsm"
            elif re.search(r"rezultate financiare", normalized_title):
                event_type = "earnings_release"
            elif re.search(r"dividend", normalized_title):
                event_type = "dividend"
            else:
                event_type = "unknown"

            # Extract period reference for certain event types
            period_reference, period_start, period_end = parse_period_reference(title) if event_type in ["earnings_release", "earnings_conf_call"] else (None, None, None)

            # Insert into the database
            cursor.execute("""
                INSERT OR IGNORE INTO financial_events 
                (company_ticker, event_date, event_type, title, description, period_reference, period_start, period_end, category, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ticker, event_date, event_type, title, description, period_reference, period_start, period_end, category, "BVB"))

            conn.commit()
            print(f"✅ Event added/updated: {title} ({event_date}) - Ticker: {ticker}, Type: {event_type}, Category: {category}")

    except sqlite3.Error as e:
        print(f"❌ Database Error: {e}")
    finally:
        conn.close()

def process_and_insert_bnr_events(bnr_events):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for event in bnr_events:
            event_type = event.get("Event type")
            # Filter only "Comunicat de presă" and convert it to "press_release"
            if "comunicat de presă" not in event_type.lower():
                print(f"⚠️ Skipping non-press release event: {event_type}")
                continue
            
            # Convert to standardized event type
            event_type = "press_release"

            # Extract and transform fields
            event_date = parse_romania_date(event.get("Date"))
            event_name = event.get("Event name")

            # Split title by dash and take only the first part
            event_title = event_name.split(" – ")[0].strip()

            # Set description as the same as the event title
            description = event_title

            # Lowercase the period reference
            period_reference = event.get("Period").lower() if event.get("Period") else "unknown"
            category = "macro"
            source = "BNR"

            # Insert into the database
            cursor.execute("""
                INSERT OR IGNORE INTO financial_events 
                (company_ticker, event_date, event_type, title, description, period_reference, category, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (None, event_date, event_type, event_title, description, period_reference, category, source))
            conn.commit()
            print(f"✅ BNR Event added: {event_title} ({event_date}) - Type: {event_type}, Period: {period_reference}")

    except sqlite3.Error as e:
        print(f"❌ Database Error while processing BNR events: {e}")
    finally:
        conn.close()

def process_and_insert_insse_events(insse_events):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for event in insse_events:
            event_date = event.get("Date")
            event_title = event.get("Event name")
            description = event_title
            period_reference = event.get("Period").lower() if event.get("Period") else "unknown"
            category = "macro"
            source = "INS"
            event_type = "press_release"

            # Insert into the database
            cursor.execute("""
                INSERT OR IGNORE INTO financial_events 
                (company_ticker, event_date, event_type, title, description, period_reference, category, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (None, event_date, event_type, event_title, description, period_reference, category, source))
            conn.commit()
            print(f"✅ INSSE Event added: {event_title} ({event_date}) - Type: {event_type}, Period: {period_reference}")

    except sqlite3.Error as e:
        print(f"❌ Database Error while processing INSSE events: {e}")
    finally:
        conn.close()


def scrape_bnr():
    driver = webdriver.Chrome()
    all_events=[] # To store all events across months
    try:
        driver.get("https://www.bnro.ro/Calendar-984.aspx")
        time.sleep(5)  # Adjust the sleep time as needed
        for month in range(12):    
            # Get page source once JavaScript has run
            page_source = driver.page_source
        
            # Parse the HTML with BeautifulSoup
            soup = BeautifulSoup(page_source, "html.parser")
            
            # Check if "No events" is present
            no_events_message=soup.find("span", id="ctl00_ctl00_CPH1_CPH1_ctl02_lblDataText")
            if no_events_message and "Nu există evenimente" in no_events_message.text:
                print(f"Stopping scrape:{no_events_message.text.strip()}")
                break #stop the loop if "No events" message found

            # Scrape the events for the current month
            events_div=soup.find("div", class_="calendarEvents")
            event_paragraphs=events_div.find_all("p")

            for pg in event_paragraphs:
                spans=pg.find_all("span")
                event=spans[0].text.strip()
                event_type=spans[1].text.strip()

                # Extract the date, event name, and period
                date_match=re.search(r"\b\d{2}\.\d{2}\.\d{4}\b", event)
                event_name=re.search(r"(?<=-\s)(.*?)(?=\s-\s|\s*$)(.*?)", event).group(1)

                # Extract info from match object
                event_date=date_match.group() if date_match else "unknown"
    
                period_match=re.search(r"\b\w+ \d{4}\b$", event)
                period=period_match.group() if period_match else "unknown"          
                print(f"🗓️ [BNR Event] Date: {event_date}, Type: {event_type}, Name: {event_name}, Period: {period}")
            
                all_events.append({
                    "Date": event_date,
                    "Event name": event_name,
                    "Period": period,
                    "Event type": event_type
                    })

            # Try to move to the next month by clicking the "Next" button
            try:
                next_month_button=driver.find_element(By.XPATH, "//a[@title='Go to the next month']")
                next_month_button.click()
                print(f"➡️ Moved to the next month.")
                time.sleep(5) # Wait for the next month's events to load

            except Exception as e:
                print(f'Failed to go to the month: {e}')
                break  # Stop the loop if we can't go to the next month
    
    except Exception as e:
        print(f"❌ Failed to scrape BNR events: {e}")
    finally:
        driver.quit()
        print("🚀 BNR Scraping complete. Browser closed.")
    print(f"✅ Total BNR Events Extracted: {len(all_events)}")
    return all_events



def scrape_insse():
    driver = webdriver.Chrome()
    events = []

    try:
        # Open the INSSE calendar page
        driver.get("https://insse.ro/cms/ro/calendar-created/year")
        time.sleep(5)

        # Extract events from the mini calendar
        soup = BeautifulSoup(driver.page_source, "html.parser")
        valid_events = soup.find_all("td", class_=lambda c: c and "mini" in c and "future" in c and "has-events" in c)

        event_filter = [
            "Lucrările de construcții",
            "Evoluția PIB",
            "Indicele prețurilor de consum (IPC)",
            "Tendințe în evoluția activității economice",
            "Șomajul BIM",
            "Resursele de energie",
            "Cifra de afaceri în serviciile de piață prestate în principal întreprinderilor",
            "Cifra de afaceri în comerț și servicii prestate în principal populației",
            "Indicii trimestriali ai costului forței de muncă",
            "Indicele prețurilor producției industriale (IPPI)",
            "Veniturile și cheltuielile gospodăriilor",
            "Cifra de afaceri în comerțul cu amănuntul",
            "Cifra de afaceri în comerțul cu ridicata",
            "Comerțul internațional cu bunuri al României",
            "Câștigul salarial mediu lunar",
            "Indicii producției industriale (IPI)", 
            "Indicii valorici ai comenzilor noi din industrie",
            "Autorizațiile de construire eliberate pentru clădiri",
            "Salariile",
            "Locurile de muncă vacante",
            "Investiții nete în economia națională"
        ]

        for event in valid_events:
            event_links = event.find_all("a")
            for event_link in event_links:
                url_level1 = urljoin(INSSE_BASE_URL, event_link.get("href"))
                driver.get(url_level1)
                time.sleep(5)
                page_content = BeautifulSoup(driver.page_source, "html.parser")
                daily_table=page_content.find("table", class_="full")

                daily_links=daily_table.find_all("a")
                for daily_link in daily_links:
                    if "/ro/" in daily_link.get("href"):
                        relative_url=daily_link.get("href")
                        url_level2=urljoin(INSSE_BASE_URL, relative_url)
                        driver = webdriver.Chrome()
                        driver.get(url_level2)
                        time.sleep(5)
                        page_final = BeautifulSoup(driver.page_source, "html.parser")

                        # Extract event details
                        x=page_final.find("h1")
                        event_name=x.text.strip()
                        # Extract event date from the "content" attribute
                        date_element = page_final.find("span", property="dc:date dc:created")
                        if date_element and date_element.get("content"):
                            event_date = date_element.get("content").split("T")[0]
                        else:
                            print(f"⚠️ Skipping event '{event_name}' with missing or malformed date")
                            continue

                        # Extract event period
                        period_elements = page_final.find_all("div", class_="field-item even")
                        if len(period_elements) > 1:
                            event_period = period_elements[1].text.strip().lower()
                        else:
                            event_period = "unknown"

                        if any(keyword.lower() in event_name.lower() for keyword in event_filter):
                            events.append({
                                "Date": event_date,
                                "Event name": event_name,
                                "Period": event_period
                            })
                            print(f"🗓️ [INSSE Event] Date: {event_date}, Title: {event_name}, Period: {event_period}")


    except Exception as e:
        print(f"❌ Error during INSSE scraping: {e}")
    finally:
        driver.quit()

    return events


def main():
    # Clear old events before starting
    clear_old_events()

    # Initialize empty event lists
    bvb_events, bnr_events, insse_events = [], [], []

    # Scrape BVB Events
    try:
        print("\n🔄 Scraping BVB Events...")
        bvb_events = scrape_bvb()
        print(f"✅ Total BVB Events Extracted: {len(bvb_events)}")
        process_and_insert_bvb_events(bvb_events)
    except Exception as e:
        print(f"❌ BVB Scraping Error: {e}")

    # Scrape BNR Events
    try:
        print("\n🔄 Scraping BNR Events...")
        bnr_events = scrape_bnr()
        print(f"✅ Total BNR Events Extracted: {len(bnr_events)}")
        process_and_insert_bnr_events(bnr_events)
    except Exception as e:
        print(f"❌ BNR Scraping Error: {e}")

    # Scrape INSSE Events
    try:
        print("\n🔄 Scraping INSSE Events...")
        insse_events = scrape_insse()
        print(f"✅ Total INSSE Events Extracted: {len(insse_events)}")
        process_and_insert_insse_events(insse_events)
    except Exception as e:
        print(f"❌ INSSE Scraping Error: {e}")

    # Final Summary
    print("\n📝 Scraping Summary:")
    print(f"✅ Total BVB Events Processed: {len(bvb_events)}")
    print(f"✅ Total BNR Events Processed: {len(bnr_events)}")
    print(f"✅ Total INSSE Events Processed: {len(insse_events)}")
    print("🚀 All Events Processed Successfully.")

if __name__ == "__main__":
    main()


