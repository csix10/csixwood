import requests
import pandas as pd
import re
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Tuple, Dict

class Jotform:
    def __init__(self):
        pass

    def _slugify(self, s: str) -> str:
        if s is None:
            return ""
        s = s.strip()
        s = re.sub(r"\s+", "_", s)
        s = re.sub(r"[^0-9a-zA-Z_]+", "", s)
        return s.lower()

    def jotform_to_dataframe(self, eu_mode: bool = True, limit: int = 1000) -> pd.DataFrame:
        api_key = "cb09ee37d76479f386088766221dfa6c"
        form_id = "252166213464049"
        """
        Jotform beküldések DataFrame-ként.
        - Hiányzó/üres answer -> None
        - Listák -> '; '-tel összefűzve
        - Dict válaszok -> több oszlopra bontva: <mezonev>.<kulcs>
        """
        base = "https://eu-api.jotform.com" if eu_mode else "https://api.jotform.com"
        url = f"{base}/form/{form_id}/submissions?apiKey={api_key}&limit={limit}"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        payload = resp.json()

        # Ha EU Safe Mode átirányítást kapnánk, jelezzünk egyértelmű hibát
        if "content" not in payload:
            msg = payload.get("message", "Váratlan API válasz.")
            raise RuntimeError(f"Jotform API hiba: {msg}")

        rows = []
        for sub in payload["content"]:
            row = {
                "submission_id": sub.get("id"),
                "created_at": sub.get("created_at"),
                "status": sub.get("status"),
            }
            answers = sub.get("answers", {}) or {}
            for qid, ans in answers.items():
                field_base = ans.get("name") or ans.get("text") or f"field_{qid}"
                field_key = self._slugify(field_base) or f"field_{qid}"

                # Ha nincs 'answer' kulcs vagy üres az érték, tegyünk None-t
                if "answer" not in ans:
                    row[field_key] = None
                    continue

                a = ans.get("answer")
                if a in ("", None) or a == [] or a == {}:
                    row[field_key] = None
                    continue

                # Típusfüggő kezelés
                if isinstance(a, dict):
                    # pl. cím mező: {city: ..., street: ...}
                    for k, v in a.items():
                        subkey = self._slugify(str(k)) or str(k)
                        row[f"{field_key}.{subkey}"] = v
                elif isinstance(a, list):
                    # pl. több választás vagy több fájl -> egy cellába fűzzük
                    row[field_key] = "; ".join(map(str, a))
                else:
                    # skalár: string/number/bool
                    row[field_key] = a

            rows.append(row)

        df = pd.DataFrame(rows)
        return df

class Utdij_kalkulator:
    def __init__(self, erkezesi_hely: str, uzemanyag_fajta="benzin", l_per_100km = 8.5, autoamortizacio_per_km = 15, indulasi_hely="Szeged, Selmeci utca 17."):
        self.uzemanyag_fajta = uzemanyag_fajta
        self.l_per_100km = l_per_100km
        self.hely_1 = indulasi_hely
        self.hely_2 = erkezesi_hely
        self.autoamortizacio_per_km = autoamortizacio_per_km

        self.ev = datetime.now().year

        self.NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
        self.OSRM_URL = "https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
        self.HEADERS = {"User-Agent": "asztalos-arajanlat/1.0"}
        self.nav_url = ""

    def nav_uzemanyag_url(self, ev: int, timeout: int = 10) -> str | None:
        base_list = "https://nav.gov.hu/ugyfeliranytu/uzemanyag"
        session = requests.Session()
        headers = {"User-Agent": "Mozilla/5.0"}

        def is_soft_404(html: str) -> bool:
            h = html.lower()
            # NAV 404 oldal tipikus szövegei
            return ("nem található" in h) or ("az ön által kért oldal" in h)

        # 1) Gyűjtőoldal letöltése
        try:
            r = session.get(base_list, timeout=timeout, headers=headers)
            r.raise_for_status()
        except requests.RequestException:
            return None

        # 2) Link kinyerése a HTML-ből (ban/ben mindkettő jó)
        m = re.search(
            rf'href="(/ugyfeliranytu/uzemanyag/{ev}-(?:ban|ben)-alkalmazhato-uzemanyagarak)"',
            r.text
        )
        if not m:
            return None

        url = "https://nav.gov.hu" + m.group(1)

        # 3) Soft-404 ellenőrzés a céloldalon
        try:
            r2 = session.get(url, timeout=timeout, headers=headers, allow_redirects=True)
            if r2.status_code != 200:
                return None
            if is_soft_404(r2.text):
                return None
            self.nav_url=r2.url
            return r2.url  # végleges (redirect utáni) URL
        except requests.RequestException:
            return None

    def nav_uzemanyag_arlista(self):
        r = requests.get(self.nav_uzemanyag_url(self.ev))
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # táblázat és sorok
        table = soup.find("table")
        rows = table.find_all("tr")

        # cellák kiszedése minden sorból
        data = []
        for row in rows:
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if cells:  # üres sorokat kihagyjuk
                data.append(cells)

        # DataFrame készítés
        df = pd.DataFrame(data[1:], columns=data[0])  # első sor a fejléc
        return df

    def aktualis_benzin_ar(self):
        df = self.nav_uzemanyag_arlista()
        if self.uzemanyag_fajta == "benzin":
            return df["ÓlmozatlanmotorbenzinESZ-95(Ft/l)"].loc[0]
        elif self.uzemanyag_fajta == "dizel":
            return df["Gázolaj(Ft/l)"].loc[0]
        else:
            print("HIBA!")
            return None

    def geocode(self, place: str) -> Tuple[float, float]:
        """Helynév/cím → (lat, lon)."""
        params = {"q": place, "format": "json", "limit": 1}
        r = requests.get(self.NOMINATIM_URL, params=params, headers=self.HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()
        if not data:
            raise ValueError(f"Nem található hely: {place}")
        return float(data[0]["lat"]), float(data[0]["lon"])

    def route_distance_time(self, origin: str, destination: str) -> Dict[str, float]:
        """Autós útvonal távolság (km) és idő (perc) OSRM-ből."""
        lat1, lon1 = self.geocode(origin)
        lat2, lon2 = self.geocode(destination)
        url = self.OSRM_URL.format(lon1=lon1, lat1=lat1, lon2=lon2, lat2=lat2)
        params = {"overview": "false", "alternatives": "false", "annotations": "false"}
        r = requests.get(url, params=params, headers=self.HEADERS, timeout=20)
        r.raise_for_status()
        js = r.json()
        if js.get("code") != "Ok" or not js.get("routes"):
            raise RuntimeError(f"OSRM nem adott útvonalat: {js.get('message')}")
        route = js["routes"][0]
        distance_km = route["distance"] / 1000.0
        duration_min = route["duration"] / 60.0
        return {"distance_km": distance_km, "duration_min": duration_min}

    def fuel_cost(self, distance_km: float) -> Dict[str, float]:
        """
        Üzemanyagköltség (HUF)
        """
        price_per_liter = float(self.aktualis_benzin_ar())
        liters = distance_km * (self.l_per_100km / 100.0)
        cost = liters * price_per_liter
        return {"koltseg": cost, "liter": liters, "literar_huf": price_per_liter}

    def utdij_kalkulacio(self, plusztav) -> Dict[str, float]:
        rt = self.route_distance_time(self.hely_1, self.hely_2)
        fogyasztas = self.fuel_cost(rt["distance_km"] + plusztav)
        amortizacio = (rt["distance_km"] + plusztav) * self.autoamortizacio_per_km
        return {
            "indulas": self.hely_1,
            "erkezes": self.hely_2,
            "tavolsag_km": round(rt["distance_km"] + plusztav, 1),
            "menetido_perc": round(rt["duration_min"]),
            "fogyasztas_l100": self.l_per_100km,
            "literar_huf": fogyasztas["literar_huf"],
            "literek": round(fogyasztas["liter"], 2),
            "uzemanyag_koltseg_huf": round(fogyasztas["koltseg"]),
            "amortizacio_per_km" : self.autoamortizacio_per_km,
            "auto_amortizacio_huf": round(amortizacio),
            "osszesen_huf": round((fogyasztas["koltseg"] + amortizacio) * 2)
        }