import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

DATE = datetime.now(ZoneInfo("Europe/Warsaw"))
DATE_ISO = DATE.strftime("%Y-%m-%d")

MONTHS = [
    "stycznia", "lutego", "marca", "kwietnia",
    "maja", "czerwca", "lipca", "sierpnia",
    "września", "października", "listopada", "grudnia"
]

DAYS = [
    "poniedziałek", "wtorek", "środę", "czwartek",
    "piątek", "sobotę", "niedzielę"
]

DATE_PL = (
    f"{DAYS[DATE.weekday()]}, "
    f"{DATE.day} {MONTHS[DATE.month - 1]} {DATE.year}"
)

URL = f"https://episkopat.pl/liturgia/{DATE_ISO}"

headers = {
    "User-Agent": "Mozilla/5.0 Ministranckie-Czytanie"
}

response = requests.get(URL, headers=headers, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")


def znajdz_naglowek(nazwy):
    for h2 in soup.find_all("h2"):
        tekst = " ".join(h2.stripped_strings).strip().lower()

        for nazwa in nazwy:
            if tekst == nazwa.lower():
                return h2

    return None


def pobierz_sekcje(nazwy):
    naglowek = znajdz_naglowek(nazwy)

    if not naglowek:
        return None

    teksty = []

    for element in naglowek.next_elements:

        if getattr(element, "name", None) == "h2":
            break

        if getattr(element, "name", None) in ["p", "blockquote"]:
            tekst = " ".join(element.stripped_strings)

            if tekst and tekst not in teksty:
                teksty.append(tekst)

    if not teksty:
        return None

    return {
        "reference": teksty[0],
        "text": "\n\n".join(teksty[1:])
    }


dane = {
    "date": DATE_ISO,
    "date_pl": DATE_PL,

    "firstReading": pobierz_sekcje([
        "Pierwsze czytanie"
    ]),

    "psalm": pobierz_sekcje([
        "Psalm responsoryjny"
    ]),

    "secondReading": pobierz_sekcje([
        "Drugie czytanie"
    ]),

    "gospel": pobierz_sekcje([
        "Ewangelia"
    ])
}

with open("readings.json", "w", encoding="utf-8") as f:
    json.dump(dane, f, ensure_ascii=False, indent=2)

print("Zapisano czytania dla:", DATE_ISO)
