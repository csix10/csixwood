from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.label import MDLabel


class FelmeresApp(MDApp):
    def __init__(self):
        super().__init__()
        self.screen = MDScreen()
        self.nev = ""  # A név tárolása

    def egyszeru_szoveg(self, szoveg, igazitas="center", pozicio={"center_y": 0.9}, stilus="Primary"):
        label = MDLabel(
            text=szoveg,
            halign=igazitas,
            pos_hint=pozicio,
            theme_text_color=stilus
        )
        self.screen.add_widget(label)

    def szoveg_input(self, szoveg, pozicio={"center_x": 0.5, "center_y": 0.6}, meret=0.8):
        name_field = MDTextField(
            hint_text=szoveg,
            pos_hint=pozicio,
            size_hint_x=meret
        )
        self.screen.add_widget(name_field)

        return name_field

    def gomb(self, szoveg, kovetkezmeny, pozicio={"center_x": 0.5, "center_y": 0.4}):
        save_button = MDRectangleFlatButton(
            text=szoveg,
            pos_hint=pozicio,
            on_release=kovetkezmeny
        )
        self.screen.add_widget(save_button)

    def mentes(self, instance):
        print(f"Mentve: {self.nev}")

    def build(self):
        self.egyszeru_szoveg("Helyszíni felmérés")
        nev_input = self.szoveg_input("Ügyfél neve")
        self.nev = nev_input.text
        self.gomb("Mentes", self.mentes)

        return self.screen


FelmeresApp().run()


