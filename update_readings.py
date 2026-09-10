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

months = [
    "stycznia", "lutego", "marca", "kwietnia",
    "maja", "czerwca", "lipca", "sierpnia",
    "września", "października", "listopada", "grudnia"
]

days = [
    "poniedziałek", "wtorek", "środa",
    "czwartek", "piątek", "sobota", "niedziela"
]

date_pl = (
    f"{days[now.weekday()]}, "
    f"{now.day} {months[now.month - 1]} {now.year}"
)


# =========================
# POBRANIE STRONY KEP
# =========================

url = f"https://episkopat.pl/liturgia/{date_iso}"

response = requests.get(
    url,
    headers={
        "User-Agent": "Mozilla/5.0"
    },
    timeout=30
)

response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# Zamieniamy stronę na zwykły tekst.
# Dzięki temu nie zależymy od tego,
# czy KEP użyje h2, div, section itd.

page_text = soup.get_text("\n", strip=True)

lines = []

for line in page_text.splitlines():
    line = line.strip()

    if line:
        lines.append(line)


# =========================
# SZUKANIE SEKCJI
# =========================

def znajdz_sekcje(start_name, stop_names):

    start_index = None

    for i, line in enumerate(lines):

        if line.rstrip(":").strip().lower() == start_name.lower():
            start_index = i
            break

    if start_index is None:
        return None

    result = []

    for line in lines[start_index + 1:]:

        clean = line.rstrip(":").strip().lower()

        if clean in [x.lower() for x in stop_names]:
            break

        # Pomijamy elementy strony, które nie są czytaniem
        if "copyright" in line.lower():
            break

        if "wygląda na to, że twoja przeglądarka" in line.lower():
            break

        if "zgłoś błąd" in line.lower():
            break

        result.append(line)

    # Usuwamy powtarzające się linie
    cleaned = []

    for line in result:

        if line not in cleaned:
            cleaned.append(line)

    if len(cleaned) < 2:
        return None

    # Pierwsza linia = sygnatura
    reference = cleaned[0]

    # Wszystko dalej = treść
    text = "\n\n".join(cleaned[1:])

    return {
        "reference": reference,
        "text": text
    }


# =========================
# CZYTANIA
# =========================

first_reading = znajdz_sekcje(
    "Pierwsze czytanie",
    [
        "Psalm responsoryjny",
        "Drugie czytanie",
        "Werset przed Ewangelią (Alleluja)",
        "Ewangelia"
    ]
)

psalm = znajdz_sekcje(
    "Psalm responsoryjny",
    [
        "Drugie czytanie",
        "Werset przed Ewangelią (Alleluja)",
        "Ewangelia"
    ]
)

second_reading = znajdz_sekcje(
    "Drugie czytanie",
    [
        "Werset przed Ewangelią (Alleluja)",
        "Ewangelia"
    ]
)

gospel = znajdz_sekcje(
    "Ewangelia",
    [
        "Patroni",
        "Homilie"
    ]
)


# =========================
# USUWANIE KOMENTARZA
# =========================

if gospel:

    text = gospel["text"]

    # Komentarz księdza zaczyna się po właściwym tekście Ewangelii.
    # Odcinamy go na charakterystycznych słowach.

    markers = [
        "Nie ma chyba w Ewangelii",
        "Miłość nieprzyjaciół nie polega",
        "„Bądźcie miłosierni"
    ]

    for marker in markers:

        position = text.find(marker)

        if position >= 0:
            text = text[:position]
            break

    gospel["text"] = text.strip()


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


print("================================")
print("AKTUALIZACJA CZYTAŃ")
print("================================")
print("Data:", date_iso)
print("Pierwsze czytanie:", bool(first_reading))
print("Psalm:", bool(psalm))
print("Drugie czytanie:", bool(second_reading))
print("Ewangelia:", bool(gospel))
print("================================")
