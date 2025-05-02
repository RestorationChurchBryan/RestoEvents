
import time
import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime, timedelta
import pytz

EVENTS_PAGE_URL = "https://restorationbryan.com/events"
TIMEZONE = pytz.timezone("America/Chicago")
SUNDAY_LOCATION = "501 W 31st St, Bryan, TX 77803"
ICS_OUTPUT_FILE = "restoration_calendar.ics"

def find_subsplash_embed_url():
    response = requests.get(EVENTS_PAGE_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    iframe = soup.find("iframe", src=lambda s: s and "embed" in s and "branding" in s)
    if iframe:
        return iframe["src"]
    return None

def parse_embed_events(embed_url):
    full_url = embed_url if embed_url.startswith("http") else "https://subsplash.com" + embed_url
    response = requests.get(full_url)
    soup = BeautifulSoup(response.text, "html.parser")

    links = [(a.get_text(strip=True), a.get("href")) for a in soup.find_all("a", href=True) if '/ev/' in a['href']]
    text = soup.get_text()

    events = []
    for text_block, href in links:
        try:
            # Attempt to extract a date from text
            date_str = next(line for line in text_block.split(" ") if any(month in line for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                                                                                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]))
            date_obj = datetime.strptime(date_str + " 2025", "%b%d %Y")  # Update year logic as needed
            event = Event()
            event.name = text_block.split(date_str)[0].strip()
            event.begin = TIMEZONE.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 18, 0))  # 6pm default
            event.end = event.begin + timedelta(hours=1)
            event.location = SUNDAY_LOCATION
            event.url = "https://subsplash.com" + href
            events.append(event)
        except Exception as e:
            continue
    return events

def add_weekly_sunday_services(calendar, weeks=12):
    today = datetime.now(TIMEZONE)
    next_sunday = today + timedelta(days=(6 - today.weekday()) % 7)
    
    for i in range(weeks):
        event_date = next_sunday + timedelta(weeks=i)
        start_time = TIMEZONE.localize(datetime(event_date.year, event_date.month, event_date.day, 10, 0))
        e = Event()
        e.name = "Sunday Service"
        e.begin = start_time
        e.end = start_time + timedelta(hours=1)
        e.location = SUNDAY_LOCATION
        calendar.events.add(e)

def main():
    embed_url = find_subsplash_embed_url()
    if not embed_url:
        print("Could not find embed URL.")
        return

    calendar = Calendar()
    events = parse_embed_events(embed_url)
    for e in events:
        calendar.events.add(e)

    add_weekly_sunday_services(calendar)

    # 30-second pause to allow Google Calendar sync if pulling raw
    print("Waiting 30 seconds before saving calendar for sync delay...")
    time.sleep(30)

    with open(ICS_OUTPUT_FILE, "w") as f:
        f.writelines(calendar)
    print(f"ICS calendar saved to {ICS_OUTPUT_FILE}")

if __name__ == "__main__":
    main()
