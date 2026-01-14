import PySide6.QtWidgets as Qw
import app.faj_beolvaso_kiirato as faj
import app.arajanlat_keszito as araj

class Front:
    def __init__(self):
        self.app = Qw.QApplication([])
        self.window = Qw.QWidget()
        self.layout = Qw.QVBoxLayout()
        self.window.setWindowTitle("CsixWood")
        self.window.resize(300, 200)

    def stilus_beallitas(self):
        self.window.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                color: white;
                font-family: 'Segoe UI';
                font-size: 16px;
            }
            QLabel {
                color: #ffcc00;
            }
            QPushButton {
                background-color: #3a3a5c;
                color: white;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #4c4c6d;
            }
        """)

    def szoveg_kiiratas(self, szoveg):
        label = Qw.QLabel(szoveg)
        self.layout.addWidget(label)

    def gomb(self, szoveg, metodus):
        button = Qw.QPushButton(szoveg)
        button.clicked.connect(metodus)
        self.layout.addWidget(button)

    def input_mezo(self, szoveg):
        nev = Qw.QLineEdit()
        nev.setPlaceholderText(szoveg)
        self.layout.addWidget(nev)
        return nev

    def ajanlat_keszites(self, vezetek_nev, kereszt_nev):
        araj.Arajanlat(vezetek_nev.text(), kereszt_nev.text()).elkeszites()

    def futtas(self):
        self.szoveg_kiiratas("Válaszd ki a szabásjegyzéket")
        vezetek_nev = self.input_mezo("Írd be az ügyfél vezetéknevét:")
        kereszt_nev = self.input_mezo("Írd be az ügyfél keresztnevét:")
        self.gomb("Árajánlat készítése", lambda: self.ajanlat_keszites(vezetek_nev, kereszt_nev))

        self.window.setLayout(self.layout)
        self.stilus_beallitas()
        self.window.show()
        self.app.exec()

if __name__ == "__main__":
    Front().futtas()




