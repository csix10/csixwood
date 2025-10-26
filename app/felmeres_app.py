from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
import csv, os
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle
from kivymd.uix.card import MDCard
from kivy.uix.scrollview import ScrollView
from kivymd.uix.list import MDList, OneLineAvatarIconListItem, IconLeftWidget
from kivymd.uix.textfield import MDTextField
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivymd.toast import toast
from plyer import camera
import shutil



class RajzTabla(Widget):
    """Egyszerű rajztábla toll- és radírmóddal."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mode = "toll"
        self.color = (0, 0, 0)
        self.width_line = 2
        self.enabled = False  # csak ha True, lehet rajzolni

        # Fehér háttér
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def on_touch_down(self, touch):
        if self.enabled and self.collide_point(*touch.pos):
            with self.canvas:
                Color(*self.color)
                touch.ud['line'] = Line(points=(touch.x, touch.y), width=self.width_line)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.enabled and 'line' in touch.ud and self.collide_point(*touch.pos):
            touch.ud['line'].points += [touch.x, touch.y]
            return True
        return super().on_touch_move(touch)

    def mod_valtas(self):
        """Toll ↔ radír váltás."""
        if self.mode == "toll":
            self.mode = "radir"
            self.color = (1, 1, 1)
            self.width_line = 25
        else:
            self.mode = "toll"
            self.color = (0, 0, 0)
            self.width_line = 2

    def torles(self):
        self.canvas.clear()
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)

class AppKellek:
    def egyszeru_szoveg(self, parent, szoveg, betustilus="Body1", igazitas="center", pozicio={"center_y": 0.9}, stilus="Primary"):
        label = MDLabel(
            text=szoveg,
            halign=igazitas,
            pos_hint=pozicio,
            theme_text_color=stilus,
            font_style=betustilus
        )
        parent.add_widget(label)

    def szoveg_input(self, parent, szoveg, pozicio={"center_x": 0.5, "center_y": 0.6}, meret=0.8):
        mező = MDTextField(
            hint_text=szoveg,
            pos_hint=pozicio,
            size_hint_x=meret
        )
        parent.add_widget(mező)
        return mező

    def gomb(self, parent, szoveg, kovetkezmeny, pozicio={"center_x": 0.5, "center_y": 0.4}):
        gomb = MDRectangleFlatButton(
            text=szoveg,
            pos_hint=pozicio,
            on_release=kovetkezmeny
        )
        parent.add_widget(gomb)
        return gomb

    def szekcio_cim(self, patern, cim):
        self.egyszeru_szoveg(patern, cim, betustilus="H6", igazitas="left")  # Kiemelt szekció cím
        patern.add_widget(
            MDBoxLayout(height=1, md_bg_color=[0.8, 0.8, 0.8, 1], size_hint_y=None))  # Elválasztó vonal
        patern.add_widget(MDBoxLayout(height=8, size_hint_y=None))  # Kisebb térköz

    def rajztabla(self, parent):
        box = MDBoxLayout(orientation="vertical", spacing=10)

        tabla = RajzTabla(size_hint=(1, 0.9))
        box.add_widget(tabla)

        # Gombok
        gomb_sor = MDBoxLayout(orientation="horizontal", size_hint_y=0.1, spacing=10, padding=10)
        mod_gomb = MDFlatButton(
            text="Radír mód",
            on_release=lambda x: self._valt_mod(tabla, mod_gomb)
        )
        gomb_sor.add_widget(mod_gomb)

        torles_gomb = MDFlatButton(
            text="Törlés",
            on_release=lambda x: tabla.torles()
        )
        gomb_sor.add_widget(torles_gomb)

        box.add_widget(gomb_sor)
        parent.add_widget(box)

        return tabla

    def _valt_mod(self, tabla, gomb):
        """Segédfüggvény a gombváltáshoz."""
        tabla.mod_valtas()
        if tabla.mode == "toll":
            gomb.text = "Radír mód"
        else:
            gomb.text = "Toll mód"

    def ugyfel_kereso(self, parent, csv_path):
        """Beolvassa az ügyfél CSV-t és létrehoz egy keresőmezőt + listát a találatokhoz."""
        self.ugyfelek = []

        # --- 1️⃣ CSV beolvasása ---
        if os.path.exists(csv_path):
            with open(csv_path, mode="r", encoding="latin1") as f:
                reader = csv.DictReader(f, delimiter=';')
                for sor in reader:
                    if sor:  # ha nem üres
                        self.ugyfelek.append(sor)
        else:
            print("⚠️ Nincs meg a fájl:", csv_path)
            return

        # --- 2️⃣ Kereső mező ---
        keresomezo = MDTextField(
            hint_text="Ügyfél keresése név alapján...",
            size_hint_x=1
        )
        parent.add_widget(keresomezo)

        # --- 3️⃣ Görgethető lista a találatoknak ---
        scroll = ScrollView(size_hint=(1, 0.8))
        lista = MDList()
        scroll.add_widget(lista)
        parent.add_widget(scroll)

        # --- 4️⃣ Frissítő függvény gépeléskor ---
        def frissit_lista(instance, value):
            lista.clear_widgets()
            keresett = value.strip().lower()
            if not keresett:
                return
            for ugyfel in self.ugyfelek:
                nev = ugyfel.get('Nev', '')  # CSV-ben legyen 'Név' oszlop
                varos = ugyfel.get('Varos', '')
                lakcim = ugyfel.get('Lakcim', '')

                if keresett in nev.lower():
                    item = OneLineAvatarIconListItem(
                        text=f"{nev} – {varos}, {lakcim}",
                        on_release=lambda x, u=ugyfel: print("✅ Kiválasztott:", u)
                    )
                    item.add_widget(IconLeftWidget(icon="account"))
                    lista.add_widget(item)
        keresomezo.bind(text=frissit_lista)

    def logo(self, parent):
        # Középre helyező layout
        logo_box = AnchorLayout(anchor_x='center', anchor_y='bottom', size_hint_y=None, height=220)

        logo = Image(
            source="C:/Users/balin/OneDrive/csixwood program/csixwood/data/logo_nevvel.png",
            size_hint=(None, None),
            size=(200, 200),
            fit_mode="contain"
        )

        logo_box.add_widget(logo)
        parent.add_widget(logo_box)

    def foto_keszites(self, parent):
        """Kamera megnyitása és kép megjelenítése az appban."""
        foto_box = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None, height=400)

        # Kép helye
        self.foto_image = Image(source="", size_hint=(1, 1), keep_ratio=True)
        foto_box.add_widget(self.foto_image)

        # Gomb a fényképezéshez
        foto_gomb = MDRectangleFlatButton(
            text="Fénykép készítése",
            pos_hint={"center_x": 0.5},
            on_release=lambda x: self._keszit_foto()
        )
        foto_box.add_widget(foto_gomb)

        parent.add_widget(foto_box)

    def _keszit_foto(self):
        """Kép készítése az eszköz kamerájával."""
        try:
            # Mentés helye
            mappa = os.path.join(os.getcwd(), "kepek")
            os.makedirs(mappa, exist_ok=True)
            kep_utvonal = os.path.join(mappa, "felmeres_foto.jpg")

            # Kamera megnyitása és mentés, ezt majd le kell cserélni!!
            #camera.take_picture(filename=kep_utvonal, on_complete=self._mutat_foto)

            shutil.copy("C:/Users/balin/OneDrive/csixwood program/csixwood/data/logo_nevvel.png", kep_utvonal)
            self._mutat_foto(kep_utvonal)

        except Exception as e:
            toast(f"Hiba a kamera megnyitásakor: {e}")

    def _mutat_foto(self, path):
        """A készített fotó megjelenítése az Image widgetben."""
        if path and os.path.exists(path):
            self.foto_image.source = path
            self.foto_image.reload()
            toast("Kép mentve és betöltve!")
        else:
            toast("Nem készült kép vagy a fájl nem található.")

# --- 1. Kezdőképernyő ---
class KezdoScreen(MDScreen, AppKellek):
    def on_pre_enter(self, *args):
        self.clear_widgets()
        layout = MDBoxLayout(orientation="vertical", spacing=20, padding=40)
        self.egyszeru_szoveg(layout, "Asztalos felmérő alkalmazás")

        self.gomb(layout, "Új ügyfél megadása", lambda x: setattr(self.manager, "current", "ugyfel"))
        self.gomb(layout, "Helyszínfelmérés", lambda x: setattr(self.manager, "current", "felmeres"))

        self.add_widget(layout)


# --- 2. Új ügyfél képernyő ---
class UgyfelScreen(MDScreen, AppKellek):
    def on_pre_enter(self, *args):
        # Alapértelmezett háttérszín beállítása a képernyőn (opcionális)
        self.md_bg_color = [0.95, 0.95, 0.95, 1]  # Világos szürke háttér a kártyák kiemeléséhez

        self.scroll = ScrollView(size_hint=(1, 1))
        # Növeltük a külső margót a jobb áttekinthetőségért
        content = MDBoxLayout(orientation="vertical", spacing=16, padding=16, size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        # 1. Cím és logó kártya
        # Egyszerűbb, de kiemelt cím
        cim_kartya = MDCard(
            orientation="vertical",
            padding=16, # Kicsit több belső térköz
            spacing=10,
            size_hint_y=None,
            adaptive_height=True,
            line_color=(0, 0, 0, 0), # Nincs vonal, ha zavaró lenne
            elevation=0
        )
        self.logo(cim_kartya)
        cim_kartya.add_widget(MDBoxLayout(height=8, size_hint_y=None))
        cim_label = MDLabel(
            text="Új megrendelő",
            halign="center",
            font_style="H5",
            bold=True
        )
        cim_kartya.add_widget(cim_label)

        content.add_widget(cim_kartya)

        # 2. Személyes adatok kártya
        adat_kartya = MDCard(
            orientation="vertical",
            padding=16,
            spacing=10,
            size_hint_y=None,
            adaptive_height=True,
            elevation=0
        )
        # Szekció cím bevezetése (kicsit eltérő betűstílus)
        self.szekcio_cim(adat_kartya,"Személyes adatok")

        # Név mező
        self.egyszeru_szoveg(adat_kartya, "Teljes név", betustilus="Subtitle2", igazitas="left")
        self.nev = self.szoveg_input(adat_kartya, "Név")

        # Lakcím szekció
        self.egyszeru_szoveg(adat_kartya, "Lakcím", betustilus="Subtitle2", igazitas="left")

        # Város és Utca egy sorban
        szovegsor = MDBoxLayout(size_hint_y=None, height=64, spacing=10)
        self.varos = self.szoveg_input(szovegsor, "Város")
        self.cim = self.szoveg_input(szovegsor, "Utca, házszám")
        adat_kartya.add_widget(szovegsor)

        # Emelet, ajtó stb.
        self.emelet_ajto = self.szoveg_input(adat_kartya, "Emelet, ajtó, csengő (opcionális)")
        content.add_widget(adat_kartya)

        # 3. Elérhetőségek kártya
        elerhetoseg_kartya = MDCard(
            orientation="vertical",
            padding=16,
            spacing=10,
            size_hint_y=None,
            adaptive_height=True,
            elevation=0
        )
        # Szekció cím bevezetése
        self.szekcio_cim(elerhetoseg_kartya, "Elérhetőségek")

        # Telefonszám
        self.egyszeru_szoveg(elerhetoseg_kartya, "Telefonszám", betustilus="Subtitle2", igazitas="left")
        self.tel = self.szoveg_input(elerhetoseg_kartya, "Telefonszám (pl. +36 30 123 4567)")

        # Email
        self.egyszeru_szoveg(elerhetoseg_kartya, "Email", betustilus="Subtitle2", igazitas="left")
        self.email = self.szoveg_input(elerhetoseg_kartya, "Email cím")
        content.add_widget(elerhetoseg_kartya)

        # 4. Gombok kártya
        gomb_kartya = MDCard(
            orientation="vertical",
            padding=16,
            spacing=10,
            size_hint_y=None,
            adaptive_height=True,
            elevation=0
        )
        gomb_sor = MDBoxLayout(size_hint_y=None, height=48, spacing=10)
        self.gomb(gomb_sor, "Mentés", self.mentes)
        self.gomb(gomb_sor, "Vissza", lambda x: setattr(self.manager, "current", "kezdo"))
        gomb_kartya.add_widget(gomb_sor)
        content.add_widget(gomb_kartya)

        self.scroll.add_widget(content)
        self.add_widget(self.scroll)

    def mentes(self, instance):
        path = os.path.expanduser("C:/Users/balin/OneDrive/asztalos_adatok/ugyfelek.csv")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([self.nev.text, self.cim.text, self.tel.text, self.email.text])
        print("Ügyfél elmentve:", self.nev.text)
        self.manager.current = "kezdo"


from kivymd.uix.label import MDLabel  # A félkövér szöveghez
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.screen import MDScreen
from kivy.uix.scrollview import ScrollView


class FelmeresScreen(MDScreen, AppKellek):
    def on_pre_enter(self, *args):
        self.clear_widgets()

        # Alapértelmezett háttérszín beállítása
        self.md_bg_color = [0.95, 0.95, 0.95, 1]  # Világos szürke háttér

        # --- ScrollView az egész tartalomhoz ---
        self.scroll = ScrollView(size_hint=(1, 1))
        # Növeltük a külső margót a jobb áttekinthetőségért (16)
        content = MDBoxLayout(orientation="vertical", spacing=16, padding=16, size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        # 1. Cím és logó kártya
        cim_kartya = MDCard(
            orientation="vertical",
            padding=16,  # Növelt padding
            spacing=10,
            size_hint_y=None,
            adaptive_height=True,  # Rugalmas magasság
            line_color=(0, 0, 0, 0),
            elevation=0
        )
        # Töröltem a cim_kartya.height = 300 fix beállítást.
        self.logo(cim_kartya)
        cim_kartya.add_widget(MDBoxLayout(height=8, size_hint_y=None))

        # Félkövér cím (MDLabel-t használva a bold=True miatt, ha az egyszerű_szöveg nem támogatja)
        try:
            # Feltételezve, hogy a self.egyszeru_szoveg támogatja a bold paramétert
            self.egyszeru_szoveg(cim_kartya, "Helyszíni felmérés", betustilus="H5", igazitas="center", bold=True)
        except:
            # Ha nem támogatja, használjunk MDLabel-t:
            cim_label = MDLabel(
                text="Helyszíni felmérés",
                halign="center",
                font_style="H5",
                bold=True
            )
            cim_kartya.add_widget(cim_label)

        content.add_widget(cim_kartya)

        # 2. Ügyfél kereső kártya (BŐSÉGES HELY A TALÁLATOKNAK)
        ugyfel_kartya = MDCard(
            orientation="vertical",
            padding=16,  # Növelt padding
            spacing=10,
            size_hint_y=None,
            adaptive_height=False,  # **Fontos:** Ezt NE állítsuk True-ra, hogy legyen hely a találatoknak
            height=300,  # **Nagyobb fix magasság** a keresési találatoknak (pl. 300)
            elevation=0
        )

        self.szekcio_cim(ugyfel_kartya, "Ügyfél keresés")

        csv_path = r"C:\Users\balin\OneDrive\csixwood program\csixwood\data\ugyfelek_adat.csv"
        self.ugyfel_kereso(ugyfel_kartya, csv_path)

        content.add_widget(ugyfel_kartya)

        # 3. Projekt adatok kártya
        adat_kartya = MDCard(
            orientation="vertical",
            padding=16,  # Növelt padding
            spacing=10,
            size_hint_y=None,
            adaptive_height=True,  # Rugalmas magasság
            elevation=0
        )
        # Töröltem az adat_kartya.height = 240 fix beállítást.

        # Projekt adatok szekció
        self.szekcio_cim(adat_kartya, "Projekt adatai")

        self.egyszeru_szoveg(adat_kartya, "Projekt neve", betustilus="Subtitle2", igazitas="left")
        self.cim = self.szoveg_input(adat_kartya, "Projekt neve")

        # Anyag és szín szekció
        self.egyszeru_szoveg(adat_kartya, "Anyag és szín", betustilus="Subtitle2", igazitas="left")
        adat_sor = MDBoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=64)  # Igazított magasság
        # Töröltem az adat_sor.height=100 fix beállítást.
        self.anyag = self.szoveg_input(adat_sor, "Anyag")
        self.szin = self.szoveg_input(adat_sor, "Szín")
        adat_kartya.add_widget(adat_sor)
        content.add_widget(adat_kartya)

        # 4. Rajztáblák Szekció
        # Csináljunk a Rajzoknak egy külön kártyát a jobb elkülönítésért
        rajzok_kartya = MDCard(
            orientation="vertical",
            padding=16,
            spacing=10,
            size_hint_y=None,
            adaptive_height=True,
            elevation=0
        )

        self.szekcio_cim(rajzok_kartya, "Rajzok és Dokumentáció")

        self.rajz_hivasok_szama = 1
        # Az _rajz_kartya_beszuras hívásokat most a rajzok_kartya-ra hívjuk
        self._rajz_kartya_beszuras(rajzok_kartya, f"{self.rajz_hivasok_szama}. rajz",
                                   rajz_attr=f"rajz_{self.rajz_hivasok_szama}",
                                   magyarazat_attr=f"magy_{self.rajz_hivasok_szama}",
                                   pozicio=self.rajz_hivasok_szama + 2)

        # A gomb is a rajzok_kartya-ba kerül (jobb UI design)
        rajz_gomb_sor = MDBoxLayout(size_hint_y=None, height=48, spacing=10)
        self.gomb(rajz_gomb_sor, "Új rajz hozzáadása",
                  lambda x: self._rajz_kartya_beszuras(rajzok_kartya, f"{self.rajz_hivasok_szama}. rajz",
                                                       rajz_attr=f"rajz_{self.rajz_hivasok_szama}",
                                                       magyarazat_attr=f"magy_{self.rajz_hivasok_szama}",
                                                       pozicio=self.rajz_hivasok_szama + 2))
        rajzok_kartya.add_widget(rajz_gomb_sor)

        content.add_widget(rajzok_kartya)

        # 5. Fotók Szekció
        fotok_kartya = MDCard(
            orientation="vertical",
            padding=16,
            spacing=10,
            size_hint_y=None,
            adaptive_height=True,
            elevation=0
        )
        self.szekcio_cim(fotok_kartya, "Helyszíni fotók")

        # A target_box a fotok_kartya része lesz
        self.target_box = MDBoxLayout(orientation="vertical", spacing=10, padding=0)
        fotok_kartya.add_widget(self.target_box)

        self.foto_hivasok_szama = 1

        # A gomb is a fotok_kartya-ba kerül
        foto_gomb_sor = MDBoxLayout(size_hint_y=None, height=48, spacing=10)
        self.gomb(foto_gomb_sor, "Új fotó hozzáadása", lambda x: self._foto_kartya_beszurasa(self.target_box,
                                                                                             pozicio=self.foto_hivasok_szama))

        fotok_kartya.add_widget(foto_gomb_sor)

        content.add_widget(fotok_kartya)

        # 6. Alsó gombsor
        gomb_kartya = MDCard(
            orientation="vertical",
            padding=16,
            spacing=10,
            size_hint_y=None,
            adaptive_height=True,
            elevation=0
        )
        gombsor = MDBoxLayout(size_hint_y=None, height=48, spacing=10)  # Igazított magasság
        self.gomb(gombsor, "Mentés", lambda x: self._mentes_png())
        self.gomb(gombsor, "Vissza", lambda x: setattr(self.manager, "current", "kezdo"))
        gomb_kartya.add_widget(gombsor)
        content.add_widget(gomb_kartya)

        self.scroll.add_widget(content)
        self.add_widget(self.scroll)

    def _rajz_kartya_beszuras(self, parent, cim, rajz_attr, magyarazat_attr, pozicio):
        """Létrehoz egy rajzkártyát rajztáblával, magyarázó mezővel és rajzoló/görgető gombbal."""
        kartya = MDCard(orientation="vertical", padding=12, spacing=8, size_hint_y=None)
        kartya.md_bg_color = (1, 1, 1, 1)

        # Rajztábla mérete
        rajz_magassag = 800
        kartya.height = rajz_magassag + 250  # kicsit nagyobb, hogy a gombok is elférjenek

        # Cím
        '''
        cim_label = MDLabel(
            text=cim,
            halign="left",
            font_style="Subtitle1",
            size_hint_y=None,
            height=30
        )
        kartya.add_widget(cim_label)
        '''
        self.szekcio_cim(kartya, cim)

        # Rajztábla
        rajz = RajzTabla(size_hint=(1, None), height=rajz_magassag)
        kartya.add_widget(rajz)
        setattr(self, rajz_attr, rajz)

        # Rajztábla gombok (Radír / Törlés)
        gomb_sor = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=40, spacing=10)
        mod_gomb = MDFlatButton(
            text="Radír mód",
            on_release=lambda x: self._valt_mod(rajz, mod_gomb)
        )
        gomb_sor.add_widget(mod_gomb)

        torles_gomb = MDFlatButton(
            text="Törlés",
            on_release=lambda x: rajz.torles()
        )
        gomb_sor.add_widget(torles_gomb)
        kartya.add_widget(gomb_sor)

        # Rajzolás engedélyezése / görgetés visszaállítása
        kapcsolo_sor = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=40, spacing=10)
        rajz_gomb = MDRectangleFlatButton(
            text="Rajzolás engedélyezése",
            on_release=lambda x, r=rajz: self._rajz_mod(r)
        )
        kapcsolo_sor.add_widget(rajz_gomb)

        vissza_gomb = MDRectangleFlatButton(
            text="Görgetés engedélyezése",
            on_release=lambda x, r=rajz: self._scroll_mod(r)
        )
        kapcsolo_sor.add_widget(vissza_gomb)

        kartya.add_widget(kapcsolo_sor)

        # Magyarázó mező
        magy = self.szoveg_input(kartya, "Magyarázat", meret=1)
        setattr(self, magyarazat_attr, magy)

        # Ha a pozíció nagyobb, mint a meglévő widgetek száma, tegyük a végére
        pozicio = min(pozicio, len(parent.children))

        # ⚠️ Fontos: a Kivy a children listát fordítva tárolja!
        # Azaz: a vizuálisan „első” elem valójában a lista végén van.
        valodi_index = len(parent.children) - pozicio

        self.rajz_hivasok_szama += 1

        parent.add_widget(kartya, index=valodi_index)

    def _scroll_mod(self, rajz):
        """Visszaállítja a ScrollView-t, rajzolás tiltva."""
        rajz.enabled = False
        if hasattr(self, "scroll"):
            self.scroll.do_scroll_y = True
        print("Görgetés engedélyezve. Rajzolás letiltva.")

    def _rajz_mod(self, rajz):
        """Átkapcsol rajzoló módra, ScrollView tiltva."""
        rajz.enabled = True
        if hasattr(self, "scroll"):
            self.scroll.do_scroll_y = False
        rajz.mode = "toll"
        rajz.color = (0, 0, 0)
        rajz.width_line = 2
        print("Rajzoló mód engedélyezve. Görgetés letiltva.")

    def _foto_kartya_beszurasa(self, parent, pozicio=0):
        """Új fotókártyát szúr be a parent layoutba a megadott pozícióra."""

        foto_kartya = MDCard(
            orientation="vertical",
            padding=12,
            spacing=8,
            size_hint_y=None
        )
        foto_kartya.height = 500

        '''
        cim_label = MDLabel(
            text=f"{self.foto_hivasok_szama}. fotó",
            halign="left",
            font_style="Subtitle1",
            size_hint_y=None,
            height=30
        )
        foto_kartya.add_widget(cim_label)
        '''
        self.szekcio_cim(foto_kartya,f"{self.foto_hivasok_szama}. fotó")
        self.foto_keszites(foto_kartya)

        self.foto_hivasok_szama += 1

        # Ha a pozíció nagyobb, mint a meglévő widgetek száma, tegyük a végére
        pozicio = min(pozicio, len(parent.children))

        # ⚠️ Fontos: a Kivy a children listát fordítva tárolja!
        # Azaz: a vizuálisan „első” elem valójában a lista végén van.
        valodi_index = len(parent.children) - pozicio

        parent.add_widget(foto_kartya, index=valodi_index)

        print(f" Új fotókártya beszúrva a {pozicio}. pozícióra (valódi index: {valodi_index})")

    def _mentes_png(self):
        mappa = "C:/Users/csiki/OneDrive/asztalos_adatok/rajzok"
        os.makedirs(mappa, exist_ok=True)
        for i, rajz in enumerate([self.rajz_1, self.rajz_2], start=1):
            if hasattr(self, f"rajz_{i}"):
                path = os.path.join(mappa, f"rajz_{i}.png")
                rajz.export_png(path)
                print(f"Rajz {i} mentve: {path}")
        print("✅ Minden rajz elmentve!")


# --- Fő alkalmazás ---
class FelmeresApp(MDApp):
    def build(self):
        sm = MDScreenManager()
        sm.add_widget(KezdoScreen(name="kezdo"))
        sm.add_widget(UgyfelScreen(name="ugyfel"))
        sm.add_widget(FelmeresScreen(name="felmeres"))
        return sm


FelmeresApp().run()
