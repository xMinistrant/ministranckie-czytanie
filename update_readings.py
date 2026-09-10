import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

now = datetime.now(ZoneInfo("Europe/Warsaw"))
date = now.strftime("%Y-%m-%d")

url = f"https://episkopat.pl/liturgia/{date}"

response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30
)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")


def pobierz(naglowek):
    h = soup.find(
        lambda tag:
        tag.name in ["h2", "h3"] and
        naglowek.lower() in tag.get_text(" ", strip=True).lower()
    )

    if not h:
        return None

    tekst = []

    for element in h.find_all_next():

        if element.name in ["h2", "h3"] and element != h:
            break

        if element.name == "p":
            t = element.get_text(" ", strip=True)

            if not t:
                continue

            if "Copyright" in t:
                break

            if "JavaScript" in t:
                break

            if "Zgłoś błąd" in t:
                break

            tekst.append(t)

    if not tekst:
        return None

    return {
        "reference": tekst[0],
        "text": "\n\n".join(tekst[1:])
    }


dane = {
    "date": date,
    "date_pl": now.strftime("%A, %d.%m.%Y"),

    "firstReading": pobierz("Pierwsze czytanie"),
    "psalm": pobierz("Psalm"),
    "secondReading": pobierz("Drugie czytanie"),
    "gospel": pobierz("Ewangelia")
}


with open("readings.json", "w", encoding="utf-8") as f:
    json.dump(dane, f, ensure_ascii=False, indent=2)

print("Zaktualizowano czytania:", date)
