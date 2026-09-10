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
    "poniedziałek", "wtorek", "środa",
    "czwartek", "piątek", "sobota", "niedziela"
]

date_pl = f"{days[now.weekday()]}, {now.day} {months[now.month - 1]} {now.year}"

# =========================
# STRONA KEP
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


# =========================
# POMOCNICZA FUNKCJA
# =========================

def clean(text):
    return " ".join(text.split()).strip()


def pobierz_sekcje(tytul):
    """
    Szuka dokładnego H2, np. 'Pierwsze czytanie',
    a następnie pobiera elementy znajdujące się
    pomiędzy tym H2 a następnym H2.
    """

    heading = None

    for h2 in soup.find_all("h2"):
        tekst = clean(h2.get_text(" ", strip=True))

        if tekst.rstrip(":").lower() == tytul.lower():
            heading = h2
            break

    if heading is None:
        return None

    elementy = []

    # Idziemy po kolejnych elementach strony
    for element in heading.find_all_next():

        # Następny H2 = koniec tej sekcji
        if element.name == "h2" and element != heading:
            break

        # Interesują nas paragrafy
        if element.name != "p":
            continue

        tekst = clean(element.get_text(" ", strip=True))

        if not tekst:
            continue

        # Pomijamy techniczne elementy strony
        if "Copyright ©" in tekst:
            break

        if "Wygląda na to, że Twoja przeglądarka" in tekst:
            break

        if "Zgłoś błąd" in tekst:
            break

        elementy.append(tekst)

    if not elementy:
        return None

    # Pierwszy element = signtura
    reference = elementy[0]

    # Pozostałe = właściwa treść
    text = "\n\n".join(elementy[1:])

    return {
        "reference": reference,
        "text": text
    }


# =========================
# CZYTANIA
# =========================

first_reading = pobierz_sekcje("Pierwsze czytanie")

psalm = pobierz_sekcje("Psalm responsoryjny")

second_reading = pobierz_sekcje("Drugie czytanie")

gospel = pobierz_sekcje("Ewangelia")


# =========================
# DANE
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

with open("readings.json", "w", encoding="utf-8") as file:
    json.dump(
        data,
        file,
        ensure_ascii=False,
        indent=2
    )

print("Zaktualizowano:", date_iso)
print("Pierwsze czytanie:", bool(first_reading))
print("Psalm:", bool(psalm))
print("Drugie czytanie:", bool(second_reading))
print("Ewangelia:", bool(gospel))
