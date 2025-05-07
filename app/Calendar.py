from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import re
import pandas as pd
import requests
from urllib import request
from urllib.parse import urljoin

driver = webdriver.Chrome()
driver.get("https://insse.ro/cms/ro/calendar-created/year")
time.sleep(5)  # Adjust the sleep time as needed
page_source = driver.page_source
soup = BeautifulSoup(page_source, "html.parser")


events=[]
events_table=soup.find("table", class_="mini")
valid_events = soup.find_all("td", class_=lambda c: c and "mini" in c and "future" in c and "has-events" in c)

base_url="https://insse.ro" 

event_filter=[
    "Construction works",
    "Consumer price index",
    "Trends in the evolution of economic activity",
    "ILO Unemployment",
    "Energy resources",
    "Turnover of services rendered mainly to enterprises",
    "Turnover in services provided to the population",
    "Costul forței de muncă",
    "Industrial production prices index",
    "Household income and expenditure",
    "Turnover in retail trade",
    "Foreign trade",
    "Gross domestic product",
    "Monthly average earning",
    "Industrial production indices ", 
    "Value indices of industrial new orders",
    "Construction permits released for buildings",
    "Salariile",
    "Job vacancies"
]

# Scraping through the events and extracting data
for event in valid_events:
    event_links=event.find_all("a")
    for event_link in event_links:
        url_level1=event_link.get("href")
        driver = webdriver.Chrome()
        driver.get(url_level1)
        time.sleep(5)  
        page_content = BeautifulSoup(driver.page_source, "html.parser")
        daily_table=page_content.find("table", class_="full")
        daily_links=daily_table.find_all("a")
        for daily_link in daily_links:
            if "/en/" in daily_link.get("href"):
                relative_url=daily_link.get("href")
                url_level2=urljoin(base_url, relative_url)
                driver = webdriver.Chrome()
                driver.get(url_level2)
                time.sleep(5)
                page_final = BeautifulSoup(driver.page_source, "html.parser")

                # Extract event details
                x=page_final.find("h1")
                event_name=x.text.strip()
                y=page_final.find("span", property="dc:date dc:created")
                event_date=y.text.strip(" - 9:00am")
                z=page_final.find_all("div", class_="field-item even")
                event_period=z[1].text.strip()

                # Append the data to the events list
                events.append({
                    "Date": event_date,
                    "Event name": event_name,
                    "Period": event_period
                })

# Quit the driver after the loop               
driver.quit()

# Create a pandas DataFrame from the collected events
df=pd.DataFrame(events)

# Perform filtering using pandas
filtered_df=df[df['Event name'].str.contains('|'.join(event_filter), case=False)]

print(filtered_df)

df.to_csv("ins_events_en.csv", index=False, encoding='utf-8-sig')

filtered_df.to_csv("ins_events_en_filtered.csv", index=False,encoding='utf-8-sig')