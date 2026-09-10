import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

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

date_pl = (
    f"{days[now.weekday()]}, "
    f"{now.day} {months[now.month - 1]} {now.year}"
)

url = f"https://episkopat.pl/liturgia/{date_iso}"

response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30
)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")


def pobierz_sekcje(naglowek_tekst):
    naglowek = None

    # Szukamy dokładnego nagłówka H2
    for h2 in soup.find_all("h2"):
        tekst = " ".join(h2.stripped_strings).strip()

        if tekst.lower().rstrip(":") == naglowek_tekst.lower():
            naglowek = h2
            break

    if naglowek is None:
        return None

    # Bierzemy elementy pomiędzy tym nagłówkiem
    # a następnym H2
    elementy = []
    rodzic = naglowek.parent

    if rodzic is None:
        return None

    for element in rodzic.find_all(["p", "div"], recursive=True):
        tekst = " ".join(element.stripped_strings).strip()

        if not tekst:
            continue

        # Odrzucamy komentarze i techniczne elementy
        if "Copyright" in tekst:
            continue

        if "Wygląda na to, że Twoja przeglądarka" in tekst:
            continue

        if "Zgłoś błąd" in tekst:
            continue

        elementy.append(tekst)

    # Usuwamy duplikaty
    czyste = []
    for tekst in elementy:
        if tekst not in czyste:
            czyste.append(tekst)

    if len(czyste) == 0:
        return None

    # Pierwszy tekst = sygnatura
    reference = czyste[0]

    # Reszta = tekst czytania
    text = "\n\n".join(czyste[1:])

    return {
        "reference": reference,
        "text": text
    }


first_reading = pobierz_sekcje("Pierwsze czytanie")
psalm = pobierz_sekcje("Psalm responsoryjny")
second_reading = pobierz_sekcje("Drugie czytanie")
gospel = pobierz_sekcje("Ewangelia")


data = {
    "date": date_iso,
    "date_pl": date_pl,
    "firstReading": first_reading,
    "psalm": psalm,
    "secondReading": second_reading,
    "gospel": gospel
}


with open("readings.json", "w", encoding="utf-8") as f:
    json.dump(
        data,
        f,
        ensure_ascii=False,
        indent=2
    )

print("Zaktualizowano czytania:", date_iso)
print("Pierwsze:", bool(first_reading))
print("Psalm:", bool(psalm))
print("Drugie:", bool(second_reading))
print("Ewangelia:", bool(gospel))
