import app.arajanlat_keszito as araj
import app.faj_beolvaso_kiirato as faj
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Qt


class MunkafolyamatValasztoExcel(Qw.QGroupBox):
    """
    Excelből beolvasott munkadíj adatbázisból válogató:
    - kereső mező
    - találatok táblázatban (nev/leiras/szamtip/ar)
    - kiválasztottak táblázatban (ugyanaz)
    """
    def __init__(self, munkadij_df):
        super().__init__("Munkafolyamatok kiválasztása (munkadíj adatbázisból)")
        self.df = munkadij_df.reset_index(drop=True)

        main = Qw.QVBoxLayout(self)

        # Kereső
        self.search = Qw.QLineEdit()
        self.search.setPlaceholderText("Keresés (név/leírás), pl: gyalulás, lakk, beszerelés...")
        main.addWidget(self.search)

        # Két táblázat egymás mellett + gombok
        row = Qw.QHBoxLayout()
        main.addLayout(row)

        # Találatok
        left = Qw.QVBoxLayout()
        left.addWidget(Qw.QLabel("Találatok:"))
        self.tbl_results = Qw.QTableWidget()
        self._setup_table(self.tbl_results)
        left.addWidget(self.tbl_results)
        row.addLayout(left, 4)

        # Gombok
        mid = Qw.QVBoxLayout()
        self.btn_add = Qw.QPushButton("Hozzáadás →")
        self.btn_remove = Qw.QPushButton("← Törlés")
        self.btn_up = Qw.QPushButton("Fel ↑")
        self.btn_down = Qw.QPushButton("Le ↓")
        mid.addStretch(1)
        mid.addWidget(self.btn_add)
        mid.addWidget(self.btn_remove)
        mid.addSpacing(12)
        mid.addWidget(self.btn_up)
        mid.addWidget(self.btn_down)
        mid.addStretch(1)
        row.addLayout(mid, 1)

        # Kiválasztottak
        right = Qw.QVBoxLayout()
        right.addWidget(Qw.QLabel("Kiválasztott munkafolyamatok:"))
        self.tbl_selected = Qw.QTableWidget()
        self._setup_table(self.tbl_selected)
        right.addWidget(self.tbl_selected)
        row.addLayout(right, 4)

        # Események
        self.search.textChanged.connect(self.refresh_results)
        self.btn_add.clicked.connect(self.add_current)
        self.btn_remove.clicked.connect(self.remove_current)
        self.btn_up.clicked.connect(lambda: self.move_selected(-1))
        self.btn_down.clicked.connect(lambda: self.move_selected(+1))

        self.tbl_results.cellDoubleClicked.connect(lambda *_: self.add_current())

        # Első feltöltés
        self.refresh_results()

    def _setup_table(self, tbl: Qw.QTableWidget):
        tbl.setColumnCount(4)
        tbl.setHorizontalHeaderLabels(["Név", "Leírás", "Számítási típus", "Ár (Ft)"])
        tbl.setEditTriggers(Qw.QAbstractItemView.NoEditTriggers)
        tbl.setSelectionBehavior(Qw.QAbstractItemView.SelectRows)
        tbl.setSelectionMode(Qw.QAbstractItemView.SingleSelection)
        tbl.horizontalHeader().setStretchLastSection(True)
        tbl.verticalHeader().setVisible(False)

    def refresh_results(self):
        text = self.search.text().strip().lower()

        if not text:
            filtered = self.df
        else:
            mask = (
                self.df["nev"].str.lower().str.contains(text, na=False) |
                self.df["leiras"].str.lower().str.contains(text, na=False)
            )
            filtered = self.df[mask]

        self._fill_table(self.tbl_results, filtered)

    def _safe_str(self, x) -> str:
        if x is None:
            return ""
        # pandas NaN felismerés
        try:
            import pandas as pd
            if pd.isna(x):
                return ""
        except Exception:
            pass
        return str(x)

    def _fill_table(self, tbl: Qw.QTableWidget, df):
        tbl.setRowCount(len(df))

        for r, (_, row) in enumerate(df.iterrows()):
            tbl.setItem(r, 0, Qw.QTableWidgetItem(self._safe_str(row.get("nev", ""))))
            tbl.setItem(r, 1, Qw.QTableWidgetItem(self._safe_str(row.get("leiras", ""))))
            tbl.setItem(r, 2, Qw.QTableWidgetItem(self._safe_str(row.get("szamtip", ""))))

            # ár: legyen int, de biztonságosan
            try:
                ar_val = int(float(row.get("ar", 0) or 0))
            except Exception:
                ar_val = 0

            ar_item = Qw.QTableWidgetItem(str(ar_val))
            ar_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            tbl.setItem(r, 3, ar_item)

        tbl.resizeColumnsToContents()

    def _row_to_key(self, nev, leiras, szamtip):
        # egyedi azonosító: név + leírás + számítási típus
        return (nev.strip(), leiras.strip(), szamtip.strip())

    def add_current(self):
        r = self.tbl_results.currentRow()
        if r < 0:
            return

        nev = self.tbl_results.item(r, 0).text()
        leiras = self.tbl_results.item(r, 1).text()
        szamtip = self.tbl_results.item(r, 2).text()
        ar = self.tbl_results.item(r, 3).text()

        key = self._row_to_key(nev, leiras, szamtip)

        # duplikáció tiltás
        existing_keys = set()
        for i in range(self.tbl_selected.rowCount()):
            k = self._row_to_key(
                self.tbl_selected.item(i, 0).text(),
                self.tbl_selected.item(i, 1).text(),
                self.tbl_selected.item(i, 2).text(),
            )
            existing_keys.add(k)

        if key in existing_keys:
            return

        # hozzáadás a selected táblához
        new_row = self.tbl_selected.rowCount()
        self.tbl_selected.insertRow(new_row)
        self.tbl_selected.setItem(new_row, 0, Qw.QTableWidgetItem(nev))
        self.tbl_selected.setItem(new_row, 1, Qw.QTableWidgetItem(leiras))
        self.tbl_selected.setItem(new_row, 2, Qw.QTableWidgetItem(szamtip))
        ar_item = Qw.QTableWidgetItem(ar)
        ar_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tbl_selected.setItem(new_row, 3, ar_item)

        self.tbl_selected.resizeColumnsToContents()

    def remove_current(self):
        r = self.tbl_selected.currentRow()
        if r >= 0:
            self.tbl_selected.removeRow(r)

    def move_selected(self, direction: int):
        r = self.tbl_selected.currentRow()
        if r < 0:
            return
        nr = r + direction
        if nr < 0 or nr >= self.tbl_selected.rowCount():
            return

        # sor csere (itemek swap)
        for c in range(self.tbl_selected.columnCount()):
            a = self.tbl_selected.takeItem(r, c)
            b = self.tbl_selected.takeItem(nr, c)
            self.tbl_selected.setItem(r, c, b)
            self.tbl_selected.setItem(nr, c, a)

        self.tbl_selected.setCurrentCell(nr, 0)

    def get_selected_steps(self) -> list[dict]:
        """Kiválasztott lépések listája dict-ekben."""
        out = []
        for i in range(self.tbl_selected.rowCount()):
            out.append({
                "nev": self.tbl_selected.item(i, 0).text(),
                "leiras": self.tbl_selected.item(i, 1).text(),
                "szamtip": self.tbl_selected.item(i, 2).text(),
                "ar": int(self.tbl_selected.item(i, 3).text()) if self.tbl_selected.item(i, 3) else 0,
            })
        return out


class Front:
    def __init__(self):
        self.app = Qw.QApplication([])
        self.window = Qw.QWidget()
        self.layout = Qw.QVBoxLayout()
        self.window.setWindowTitle("CsixWood")
        self.window.resize(1000, 500)
        self.munka_widget=""

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

    def ajanlat_keszites(self, vezetek_nev, kereszt_nev, lepesek):
        araj.Arajanlat(vezetek_nev.text(), kereszt_nev.text(), lepesek).elkeszites()

    def futtas(self):
        self.szoveg_kiiratas("Válaszd ki a szabásjegyzéket")
        vezetek_nev = self.input_mezo("Írd be az ügyfél vezetéknevét:")
        kereszt_nev = self.input_mezo("Írd be az ügyfél keresztnevét:")

        link = "https://1drv.ms/x/c/595ECD328626FCDE/IQBQc2FuUwOMRp7xoE1-idfeAb-lcS22MI8C1r-XFIJB5cE?e=JHUQ2u"
        munkadij_df = faj.BeolvasKiirat().excel_beolvas_onedrive_linkbol(
            megosztasi_link=link,
            cel_mappa="data",
            fajlnev="munkadij.xlsx"
        )

        # ✅ legyen self, hogy később is elérd
        self.munka_widget = MunkafolyamatValasztoExcel(munkadij_df)
        self.layout.addWidget(self.munka_widget)

        # ✅ gombnyomáskor kérdezzük le
        self.gomb(
            "Árajánlat készítése",
            lambda: self.ajanlat_keszites(
                vezetek_nev,
                kereszt_nev,
                self.munka_widget.get_selected_steps()
            )
        )

        self.window.setLayout(self.layout)
        self.stilus_beallitas()
        self.window.show()
        self.app.exec()


if __name__ == "__main__":
    Front().futtas()




