import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# DATA
# =========================

now = datetime.now(ZoneInfo("Europe/Warsaw"))
date_iso = now.strftime("%Y-%m-%d")

days = [
    "poniedziałek", "wtorek", "środa",
    "czwartek", "piątek", "sobota", "niedziela"
]

months = [
    "stycznia", "lutego", "marca", "kwietnia",
    "maja", "czerwca", "lipca", "sierpnia",
    "września", "października", "listopada", "grudnia"
]

date_pl = (
    f"{days[now.weekday()]}, "
    f"{now.day} {months[now.month - 1]} {now.year}"
)

# =========================
# POBIERZ STRONĘ
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
# ZNAJDŹ KONKRETNY NAGŁÓWEK
# =========================

def find_heading(text):
    for tag in soup.find_all(["h2", "h3", "h4"]):
        value = " ".join(tag.stripped_strings).strip()

        if value.rstrip(":").strip().lower() == text.lower():
            return tag

    return None


# =========================
# POBIERZ ZAWARTOŚĆ
# =========================

def get_section(title, next_titles):

    heading = find_heading(title)

    if heading is None:
        print("NIE ZNALEZIONO:", title)
        return None

    parts = []

    # Idziemy po elementach rodzica nagłówka
    current = heading

    while current:

        current = current.find_next()

        if current is None:
            break

        # Następny nagłówek kończy sekcję
        if current.name in ["h2", "h3", "h4"]:

            heading_text = " ".join(
                current.stripped_strings
            ).strip().rstrip(":").lower()

            if heading_text in [x.lower() for x in next_titles]:
                break

        # Bierzemy tekst z paragrafów
        if current.name == "p":

            text = " ".join(
                current.stripped_strings
            ).strip()

            if not text:
                continue

            # Pomijamy elementy techniczne
            if "Copyright" in text:
                break

            if "Wygląda na to" in text:
                break

            if "Zgłoś błąd" in text:
                break

            parts.append(text)

    # Usuwamy duplikaty
    result = []

    for p in parts:
        if p not in result:
            result.append(p)

    if not result:
        return None

    # Pierwsza linia = sygnatura
    reference = result[0]

    # Reszta = pełny tekst
    text = "\n\n".join(result[1:])

    return {
        "reference": reference,
        "text": text
    }


# =========================
# ODCZYT CZYTAŃ
# =========================

first_reading = get_section(
    "Pierwsze czytanie",
    [
        "Psalm responsoryjny",
        "Werset przed Ewangelią (Alleluja)",
        "Ewangelia"
    ]
)

psalm = get_section(
    "Psalm responsoryjny",
    [
        "Werset przed Ewangelią (Alleluja)",
        "Ewangelia"
    ]
)

second_reading = get_section(
    "Drugie czytanie",
    [
        "Psalm responsoryjny",
        "Werset przed Ewangelią (Alleluja)",
        "Ewangelia"
    ]
)

gospel = get_section(
    "Ewangelia",
    [
        "Patroni",
        "Liturgia na dzień"
    ]
)


# =========================
# WYNIK
# =========================

data = {
    "date": date_iso,
    "date_pl": date_pl,
    "firstReading": first_reading,
    "psalm": psalm,
    "secondReading": second_reading,
    "gospel": gospel
}


# =========================
# ZAPIS
# =========================

with open(
    "readings.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        data,
        file,
        ensure_ascii=False,
        indent=2
    )


print()
print("================================")
print("AKTUALIZACJA CZYTAŃ")
print("================================")
print("Data:", date_iso)
print("Pierwsze czytanie:", bool(first_reading))
print("Psalm:", bool(psalm))
print("Drugie czytanie:", bool(second_reading))
print("Ewangelia:", bool(gospel))
print("================================")
