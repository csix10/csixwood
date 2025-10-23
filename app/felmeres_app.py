from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.textfield import MDTextField
from kivy.uix.widget import Widget
from kivy.graphics import Fbo, Color, Rectangle, Line, ClearBuffers, ClearColor
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRectangleFlatButton
from kivymd.uix.label import MDLabel
import csv, os
from kivy.core.window import Window

from kivy.uix.widget import Widget
from kivy.clock import Clock


from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle

class RajzTabla(Widget):
    """Egyszerű rajztábla toll- és radírmóddal."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mode = "toll"
        self.color = (0, 0, 0)
        self.width_line = 2

        # Fehér háttér, csak a widget területén
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            with self.canvas:
                Color(*self.color)
                touch.ud['line'] = Line(points=(touch.x, touch.y), width=self.width_line)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if 'line' in touch.ud and self.collide_point(*touch.pos):
            touch.ud['line'].points += [touch.x, touch.y]
            return True
        return super().on_touch_move(touch)

    def mod_valtas(self):
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
    def egyszeru_szoveg(self, parent, szoveg, igazitas="center", pozicio={"center_y": 0.9}, stilus="Primary"):
        label = MDLabel(
            text=szoveg,
            halign=igazitas,
            pos_hint=pozicio,
            theme_text_color=stilus
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
        """Rajztábla létrehozása gombokkal."""
        box = MDBoxLayout(orientation="vertical", spacing=10)

        # Rajztábla objektum
        tabla = RajzTabla(size_hint=(1, 0.9))
        box.add_widget(tabla)

        # Gombok sorba rendezve
        gomb_sor = MDBoxLayout(orientation="horizontal", size_hint_y=0.1, spacing=10, padding=10)

        # Toll/Radír váltó gomb
        mod_gomb = MDFlatButton(
            text="Radír mód",
            on_release=lambda x: self._valt_mod(tabla, mod_gomb)
        )
        gomb_sor.add_widget(mod_gomb)

        # Törlés gomb
        torles_gomb = MDFlatButton(
            text="Törlés",
            on_release=lambda x: tabla.torles()
        )
        gomb_sor.add_widget(torles_gomb)

        box.add_widget(gomb_sor)
        parent.add_widget(box)

    def _valt_mod(self, tabla, gomb):
        """Segédfüggvény a gombváltáshoz."""
        tabla.mod_valtas()
        if tabla.mod == "toll":
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


# --- 3. Helyszínfelmérés képernyő ---
'''
class FelmeresScreen(MDScreen, AppKellek):
    def on_pre_enter(self, *args):
        self.clear_widgets()
        layout = MDBoxLayout(orientation="vertical", spacing=10, padding=40)
        self.egyszeru_szoveg(layout, "(Itt lesz a felmérő form és rajz)")
        self.gomb(layout, "Vissza", lambda x: self.manager.current = "kezdo")
        self.add_widget(layout)
'''

class FelmeresScreen(MDScreen):
    def on_pre_enter(self, *args):
        self.clear_widgets()
        layout = MDBoxLayout(orientation="vertical", spacing=10, padding=10)

        # --- Cím ---
        layout.add_widget(
            MDLabel(
                text="Helyszíni felmérés",
                halign="center",
                theme_text_color="Primary",
                font_style="H6"
            )
        )

        # --- Rajztábla ---
        self.rajz = RajzTabla(size_hint=(1, 0.7))
        layout.add_widget(self.rajz)

        # --- Gombok alul ---
        gombsor = MDBoxLayout(size_hint_y=0.3, spacing=8, padding=8)

        # Radír / Toll váltás
        gombsor.add_widget(
            MDRectangleFlatButton(
                text="Radír/Toll",
                on_release=lambda x: self.rajz.mod_valtas()
            )
        )

        # Törlés
        gombsor.add_widget(
            MDRectangleFlatButton(
                text="Törlés",
                on_release=lambda x: self.rajz.torles()
            )
        )

        # Mentés PNG
        gombsor.add_widget(
            MDRectangleFlatButton(
                text="Mentés PNG",
                on_release=lambda x: self._mentes_png()
            )
        )

        # Vissza a kezdőképernyőre
        gombsor.add_widget(
            MDRectangleFlatButton(
                text="Vissza",
                on_release=lambda x: setattr(self.manager, "current", "kezdo")
            )
        )

        layout.add_widget(gombsor)

        self.add_widget(layout)

    def _mentes_png(self):
        """Mentés a OneDrive mappába."""
        mappa = "C:/Users/balin/OneDrive/asztalos_adatok/rajzok"
        os.makedirs(mappa, exist_ok=True)
        filepath = os.path.join(mappa, "rajz.png")
        self.rajz.export_png(filepath)
        print(f"Rajztábla elmentve: {filepath}")

# --- Fő alkalmazás ---
class FelmeresApp(MDApp):
    def build(self):
        sm = MDScreenManager()
        sm.add_widget(KezdoScreen(name="kezdo"))
        sm.add_widget(UgyfelScreen(name="ugyfel"))
        sm.add_widget(FelmeresScreen(name="felmeres"))
        return sm


FelmeresApp().run()



