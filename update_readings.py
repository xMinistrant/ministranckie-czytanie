import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# DATA
# =========================

now = datetime.now(ZoneInfo("Europe/Warsaw"))
date_iso = now.strftime("%Y-%m-%d")

months = [
    "stycznia", "lutego", "marca", "kwietnia",
    "maja", "czerwca", "lipca", "sierpnia",
    "września", "października", "listopada", "grudnia"
]

days = [
    "poniedziałek", "wtorek", "środa", "czwartek",
    "piątek", "sobota", "niedziela"
]

date_pl = f"{days[now.weekday()]}, {now.day} {months[now.month - 1]} {now.year}"

# =========================
# KEP
# =========================

url = f"https://episkopat.pl/liturgia/{date_iso}"

response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30
)

response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")


# =========================
# POBIERANIE SEKCJI
# =========================

def get_section(title):
    heading = None

    for h in soup.find_all("h2"):
        text = " ".join(h.stripped_strings).strip().lower()

        if text == title.lower():
            heading = h
            break

    if heading is None:
        return None

    items = []

    # Bierzemy tylko elementy pomiędzy tym h2
    # a następnym h2.
    for element in heading.find_all_next():

        if element.name == "h2":
            break

        if element.name not in ["p"]:
            continue

        text = " ".join(element.stripped_strings).strip()

        if not text:
            continue

        # Pomijamy przypadkowe elementy strony
        if text in items:
            continue

        items.append(text)

    if not items:
        return None

    # Pierwszy paragraf to zwykle oznaczenie,
    # np. "1 Kor 8, 1b-7. 10-13".
    reference = items[0]

    text = "\n\n".join(items[1:])

    return {
        "reference": reference,
        "text": text
    }


# =========================
# CZYTANIA
# =========================

first_reading = get_section("Pierwsze czytanie")

psalm = get_section("Psalm responsoryjny")

second_reading = get_section("Drugie czytanie")

gospel = get_section("Ewangelia")


# =========================
# ZAPIS
# =========================

data = {
    "date": date_iso,
    "date_pl": date_pl,
    "firstReading": first_reading,
    "psalm": psalm,
    "secondReading": second_reading,
    "gospel": gospel
}

with open("readings.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

print("Zapisano czytania dla:", date_iso)
