import requests
from bs4 import BeautifulSoup
import urllib.parse
import time

# --- WPISZ TUTAJ SWÓJ LINK DO WEBHOOKA DISCORDA ---
WEBHOOK_URL = "https://discord.com/api/webhooks/1562151196268044388/ti2AlDaNiwybxmIzSt44cISCS2ypsiCQlouTJqIqiQ5TsFp9Qdw6R_ic856uyTq5cl80"

def wyslij_okazje(nazwa, cena, cena_z_oplata, cena_negocjacja, stan, sprzedajacy, link, zdjecie_url="", cena_rynkowa="0", zysk_bez_neg="**Brak danych**", zysk_z_neg="**Brak danych**"):
    wykluczone_slowa = ["słuchawki", "headset", "nauszne", "dokanałowe", "gaming headset", "słuchawka"]
    nazwa_lower = nazwa.lower()
    
    for slowo in wykluczone_slowa:
        if slowo in nazwa_lower:
            print(f"Odrzucono ze względu na słuchawki: {nazwa}")
            return

    opis_tekst = (
        f"**Cena zakupu:** {cena} zł\n"
        f"**Cena całkowita z opłatą Vinted:** {cena_z_oplata} zł\n"
        f"**Cena po maksymalnej negocjacji:** {cena_negocjacja} zł\n"
        f"**Sugerowana cena sprzedaży:** **{cena_rynkowa} zł**\n"
        f"**Stan:** {stan}\n"
        f"**Sprzedający:** {sprzedajacy}\n\n"
        f"```Potencjalny zysk (BEZ NEGOCJACJI): {zysk_bez_neg}```\n"
        f"```Potencjalny zysk (MAKSYMALNA NEGOCJACJA): {zysk_z_neg}```"
    )

    embed = {
        "title": nazwa,
        "url": link,
        "description": opis_tekst,
        "color": 3447003,
        "footer": {"text": "Vinted Bot"}
    }
    
    if zdjecie_url:
        embed["image"] = {"url": zdjecie_url}

    dane = {
        "username": "Spidey Bot",
        "embeds": [embed]
    }
    
    odpowiedz = requests.post(WEBHOOK_URL, json=dane)
    if odpowiedz.status_code == 204:
        print(f"Wysłano alert: {nazwa}")
    else:
        print(f"Błąd wysyłania do Discorda (Status {odpowiedz.status_code})")

def oblicz_zysk_i_rynek(tytul, cena_zakupu_float):
    tytul_lower = tytul.lower()
    szacowana_cena_rynkowa = 0
    
    if "gothic" in tytul_lower:
        szacowana_cena_rynkowa = 200.0
    elif "ps4 pro" in tytul_lower:
        szacowana_cena_rynkowa = 900.0
    elif "ps5" in tytul_lower:
        szacowana_cena_rynkowa = 1800.0
    elif "fifa" in tytul_lower or "fc 2" in tytul_lower:
        szacowana_cena_rynkowa = 70.0
    elif "memory card" in tytul_lower or "karta pamięci" in tytul_lower:
        szacowana_cena_rynkowa = 45.0
    else:
        szacowana_cena_rynkowa = round(cena_zakupu_float * 1.3, 2)

    koszt_calkowity = cena_zakupu_float * 1.05 + 2.90
    zysk_bez = round(szacowana_cena_rynkowa - koszt_calkowity, 2)
    
    koszt_po_negocjacji = (cena_zakupu_float * 0.8) * 1.05 + 2.90
    zysk_z_neg = round(szacowana_cena_rynkowa - koszt_po_negocjacji, 2)

    if zysk_z_neg < 20.0:
        return None, None, None

    return szacowana_cena_rynkowa, f"{zysk_bez} zł", f"{zysk_z_neg} zł"

def pobierz_vinted(fraza="gry konsole"):
    fraza_url = urllib.parse.quote(fraza)
    url = f"https://www.vinted.pl/vetements?search_text={fraza_url}&order=newest_first"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "pl-PL,pl;q=0.9"
    }

    try:
        session = requests.Session()
        res = session.get(url, headers=headers)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.find_all('div', {'data-testid': 'grid-item'})
            
            if not items:
                items = soup.select('.feed-grid__item')

            print(f"Pobrano stronę Vinted! Znaleziono ogłoszeń: {len(items)}")

            for item in items[:15]:
                link_tag = item.find('a', href=True)
                if not link_tag:
                    continue
                
                link = link_tag['href']
                if not link.startswith('http'):
                    link = "https://www.vinted.pl" + link
                
                tytul = link_tag.get('title', '') or link_tag.text.strip()
                if not tytul:
                    tytul = "Gra / Konsola Vinted"

                cena_tag = item.find(string=lambda t: t and 'zł' in t)
                cena = cena_tag.strip().replace('zł', '').strip() if cena_tag else "0.0"

                try:
                    c_float = float(cena.replace(',', '.'))
                    c_oplata = round(c_float * 1.05 + 2.90, 2)
                    c_neg = round(c_float * 0.8, 2)
                except:
                    c_oplata, c_neg = cena, cena
                    c_float = 0.0

                cena_rynkowa, zysk_b, zysk_n = oblicz_zysk_i_rynek(tytul, c_float)
                if cena_rynkowa is None:
                    continue

                img_tag = item.find('img')
                zdjecie_url = ""
                if img_tag:
                    zdjecie_url = img_tag.get('src') or img_tag.get('data-src', '')

                user_tag = item.find('h4') or item.find('p')
                sprzedawca = user_tag.text.strip() if user_tag else "Użytkownik Vinted"

                wyslij_okazje(
                    nazwa=tytul,
                    cena=cena,
                    cena_z_oplata=str(c_oplata),
                    cena_negocjacja=str(c_neg),
                    stan="Używany / Dobry",
                    sprzedajacy=sprzedawca,
                    link=link,
                    zdjecie_url=zdjecie_url,
                    cena_rynkowa=str(cena_rynkowa),
                    zysk_bez_neg=zysk_b,
                    zysk_z_neg=zysk_n
                )
        else:
            print(f"Błąd połączenia ze stroną Vinted: Status {res.status_code}")

    except Exception as e:
        print(f"Wystąpił błąd: {e}")

if __name__ == "__main__":
    print("Bot uruchomiony na serwerze! Działa w trybie 24/7.")
    while True:
        pobierz_vinted("gry konsole")
        time.sleep(300)
      
