from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
import csv, os
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle
from kivymd.uix.card import MDCard
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivymd.uix.scrollview import MDScrollView

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
        self.clear_widgets()
        layout = MDBoxLayout(orientation="vertical", spacing=10, padding=40)

        self.nev = self.szoveg_input(layout, "Név")
        self.cim = self.szoveg_input(layout, "Cím")
        self.tel = self.szoveg_input(layout, "Telefonszám")
        self.email = self.szoveg_input(layout, "Email")

        self.gomb(layout, "Mentés", self.mentes)
        self.gomb(layout, "Vissza", lambda x: setattr(self.manager, "current", "kezdo"))


        self.add_widget(layout)

    def mentes(self, instance):
        path = os.path.expanduser("C:/Users/balin/OneDrive/asztalos_adatok/ugyfelek.csv")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([self.nev.text, self.cim.text, self.tel.text, self.email.text])
        print("Ügyfél elmentve:", self.nev.text)
        self.manager.current = "kezdo"

class FelmeresScreen(MDScreen, AppKellek):
    def on_pre_enter(self, *args):
        self.clear_widgets()

        # --- ScrollView az egész tartalomhoz ---
        self.scroll = ScrollView(size_hint=(1,1))
        content = MDBoxLayout(orientation="vertical", spacing=12, padding=12, size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        # Cím
        self.egyszeru_szoveg(content, "🏗️ Helyszíni felmérés", betustilus="H5", igazitas="center")

        # Projekt adatok
        adat_kartya = MDCard(orientation="vertical", padding=12, spacing=8, size_hint_y=None)
        adat_kartya.height = 120
        adat_kartya.md_bg_color = (0.97,0.97,0.97,1)
        self.egyszeru_szoveg(adat_kartya, "Projekt adatai", betustilus="Subtitle1", igazitas="left")
        self.cim = self.szoveg_input(adat_kartya, "Projekt neve")
        content.add_widget(adat_kartya)

        # Anyag / Szín sor
        self.egyszeru_szoveg(content, "Anyag és szín", betustilus="Subtitle1", igazitas="left")
        adat_sor = MDBoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=60)
        self.anyag = self.szoveg_input(adat_sor, "Anyag")
        self.szin = self.szoveg_input(adat_sor, "Szín")
        content.add_widget(adat_sor)

        # Rajztáblák
        self._rajz_kartya(content, "Első rajz", rajz_attr="rajz_1", magyarazat_attr="magy_1")
        self._rajz_kartya(content, "Második rajz", rajz_attr="rajz_2", magyarazat_attr="magy_2")

        # Alsó gombsor
        gombsor = MDBoxLayout(size_hint_y=None, height=64, spacing=10, padding=[0,6])
        self.gomb(gombsor, "💾 Mentés", lambda x: self._mentes_png())
        self.gomb(gombsor, "⬅️ Vissza", lambda x: setattr(self.manager, "current", "kezdo"))
        content.add_widget(gombsor)

        self.scroll.add_widget(content)
        self.add_widget(self.scroll)

    def _rajz_kartya(self, parent, cim, rajz_attr, magyarazat_attr):
        kartya = MDCard(orientation="vertical", padding=12, spacing=8, size_hint_y=None)
        kartya.height = 400  # egy kicsit nagyobb, hogy legyen hely a gomboknak
        kartya.md_bg_color = (1, 1, 1, 1)

        self.egyszeru_szoveg(kartya, cim, betustilus="Subtitle1", igazitas="left")

        # Rajztábla
        rajz = self.rajztabla(kartya)
        setattr(self, rajz_attr, rajz)

        # Magyarázó mező
        magy = self.szoveg_input(kartya, "Magyarázat", meret=1)
        setattr(self, magyarazat_attr, magy)

        # Gombok
        gomb_sor = MDBoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)

        # Rajzolás engedélyezése
        rajzol_gomb = MDRectangleFlatButton(
            text="Rajzolás engedélyezése",
            on_release=lambda x, r=rajz: self._rajz_mod(r)
        )
        gomb_sor.add_widget(rajzol_gomb)

        # Scroll mód engedélyezése
        scroll_gomb = MDRectangleFlatButton(
            text="Görgetés engedélyezése",
            on_release=lambda x, r=rajz: self._scroll_mod(r)
        )
        gomb_sor.add_widget(scroll_gomb)

        kartya.add_widget(gomb_sor)
        parent.add_widget(kartya)

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
