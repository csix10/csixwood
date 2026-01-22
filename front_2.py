import os
import pandas as pd
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Qt
from PySide6.QtCore import Signal
import app.arajanlat_keszito as arajanlat
import app.faj_beolvaso_kiirato as faj

# ide importáld a saját moduljaidat:
# import app.arajanlat_keszito as araj
# import app.faj_beolvaso_kiirato as faj

class MunkafolyamatValasztoExcel(Qw.QGroupBox):
    step_added = Signal(dict)   # elküldi a teljes sort: nev/leiras/szamtip/ar
    """
    Excelből beolvasott munkadíj adatbázisból válogató:
    - kereső mező
    - találatok táblázatban (nev/leiras/szamtip/ar)
    - kiválasztottak táblázatban (ugyanaz)
    """
    def __init__(self):
        super().__init__("Munkafolyamatok kiválasztása (munkadíj adatbázisból)")

        link = "https://1drv.ms/x/c/595ECD328626FCDE/IQBQc2FuUwOMRp7xoE1-idfeAb-lcS22MI8C1r-XFIJB5cE?e=JHUQ2u"
        munkadij_df = faj.BeolvasKiirat().excel_beolvas_onedrive_linkbol(
            megosztasi_link=link,
            cel_mappa="data",
            fajlnev="munkadij.xlsx"
        )

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

        # jelzés Step2-nek
        self.step_added.emit({
            "nev": nev,
            "leiras": leiras,
            "szamtip": szamtip,
            "ar": int(ar) if str(ar).strip().isdigit() else ar
        })

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


class WizardWindow(Qw.QWidget):
    def __init__(self):
        super().__init__()

        self.faj = faj.BeolvasKiirat()
        self.arajanlatszerk = arajanlat.Arajanlat()

        self.setWindowTitle("CsixWood – Árajánlat varázsló")
        self.resize(900, 600)

        self.layout = Qw.QVBoxLayout(self)

        # állapot (amit a lépések között viszünk tovább)
        self.csv_path = None
        self.anyagigeny_df = None       # anyagszükséglet (anyagjegyzék) DataFrame
        self.nyomtathato_df = None      # nyomtatható szabásjegyzék, ha kell
        self.munkalepesek = []          # kiválasztott munkafolyamatok listája (dict)
        self.hozzarendeles = {}         # {"Gyalulás": ["lucfenyo", ...]}

        # lépések
        self.stack = Qw.QStackedWidget()
        self.step1 = Step1CsvImport(self)
        self.step2 = Step2MunkaAnyag(self)
        self.step3 = Step3Export(self)

        self.stack.addWidget(self.step1)
        self.stack.addWidget(self.step2)
        self.stack.addWidget(self.step3)

        self.layout.addWidget(self.stack)

    def goto(self, idx: int):
        self.stack.setCurrentIndex(idx)
'''
class Step1CsvImport(Qw.QGroupBox):
    def __init__(self, wiz: WizardWindow):
        super().__init__("1. lépés – CSV betallózás és anyagigény számítás")
        self.wiz = wiz
        lay = Qw.QVBoxLayout(self)

        self.lbl = Qw.QLabel("Válaszd ki a szabásjegyzék CSV fájlt, majd számoljuk az anyagigényt.")
        lay.addWidget(self.lbl)

        row = Qw.QHBoxLayout()
        self.btn_run = Qw.QPushButton("Tallózás…")
        row.addWidget(self.btn_run)
        lay.addLayout(row)

        self.preview = Qw.QTableWidget()
        lay.addWidget(Qw.QLabel("Előnézet (anyagigény):"))
        lay.addWidget(self.preview, 1)

        self.btn_next = Qw.QPushButton("Tovább →")
        self.btn_next.setEnabled(False)
        lay.addWidget(self.btn_next)

        self.btn_run.clicked.connect(self.run_calc)
        self.btn_next.clicked.connect(lambda: self.wiz.goto(1))
        self.df = None

    def run_calc(self):
        self.df = self.wiz.arajanlatszerk.adatbeolvaso()
        self.wiz.arajanlatszerk.szabjegyszerk.anyagigeny_szamitasa()

        anyagigeny_df = self.wiz.arajanlatszerk.szabjegyszerk.anyagigeny

        self.wiz.anyagigeny_df = anyagigeny_df
        self.wiz.nyomtathato_df = None

        self._show_preview(anyagigeny_df)
        self.btn_next.setEnabled(True)

    def _show_preview(self, df: pd.DataFrame):
        self.preview.setRowCount(min(len(df), 15))
        self.preview.setColumnCount(len(df.columns))
        self.preview.setHorizontalHeaderLabels([str(c) for c in df.columns])

        for r in range(min(len(df), 15)):
            for c, col in enumerate(df.columns):
                self.preview.setItem(r, c, Qw.QTableWidgetItem(str(df.iloc[r, c])))
        self.preview.resizeColumnsToContents()
'''

class Step1CsvImport(Qw.QGroupBox):
    def __init__(self, wiz: "WizardWindow"):
        super().__init__("1. lépés – CSV betallózás és anyagigény számítás")
        self.wiz = wiz
        lay = Qw.QVBoxLayout(self)

        self.lbl = Qw.QLabel("1) Válaszd ki az ügyfelet  2) Tallózd be a CSV-t  3) Számoljuk az anyagigényt.")
        lay.addWidget(self.lbl)

        # ---- ÜGYFÉL VÁLASZTÓ ----
        ugyfel_box = Qw.QGroupBox("Ügyfél kiválasztása")
        ugyfel_lay = Qw.QVBoxLayout(ugyfel_box)

        self.cmb_ugyfel = Qw.QComboBox()
        self.cmb_ugyfel.setEditable(True)  # kereshető
        self.cmb_ugyfel.setInsertPolicy(Qw.QComboBox.NoInsert)
        self.cmb_ugyfel.setPlaceholderText("Kezdj el gépelni (név keresés)…")

        ugyfel_lay.addWidget(self.cmb_ugyfel)

        self.lbl_ugyfel_info = Qw.QLabel("")
        self.lbl_ugyfel_info.setWordWrap(True)
        ugyfel_lay.addWidget(self.lbl_ugyfel_info)

        lay.addWidget(ugyfel_box)

        # ---- CSV TALLÓZÁS + SZÁMÍTÁS ----
        row = Qw.QHBoxLayout()
        self.btn_run = Qw.QPushButton("CSV tallózás + számítás…")
        row.addWidget(self.btn_run)
        lay.addLayout(row)

        self.preview = Qw.QTableWidget()
        lay.addWidget(Qw.QLabel("Előnézet (anyagigény):"))
        lay.addWidget(self.preview, 1)

        self.btn_next = Qw.QPushButton("Tovább →")
        self.btn_next.setEnabled(False)
        lay.addWidget(self.btn_next)

        self.btn_run.clicked.connect(self.run_calc)
        self.btn_next.clicked.connect(lambda: self.wiz.goto(1))

        self.df = None
        self.ugyfelek_df = None

        # ügyfelek betöltése induláskor
        self._load_ugyfelek()

        # amikor ügyfelet vált, írjunk ki infót és mentsük state-be
        self.cmb_ugyfel.currentIndexChanged.connect(self._ugyfel_changed)

    def _load_ugyfelek(self):
        """
        Innen olvasod be az ügyféllistát.
        Állítsd be a saját útvonaladra!
        """
        # példa: project_root/data/ugyfelek.xlsx
        '''
        base_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(base_dir, ".."))
        data_dir = os.path.join(project_root, "data")
        path = os.path.join(data_dir, "ugyfelek.xlsx")
        

        if not os.path.exists(path):
            self.lbl_ugyfel_info.setText(f"⚠️ Nem találom az ügyféllistát: {path}")
            return
        '''

        #try:
        link = "https://1drv.ms/x/c/595ECD328626FCDE/IQCAAzRsxtjJRJhSfNq79RZ8AWpcUCbT_AV30IeTavTymUc?e=lrUfMC"
        self.ugyfelek_df = self.wiz.faj.excel_beolvas_onedrive_linkbol(megosztasi_link=link, cel_mappa="data",fajlnev="ugyfelek_adat.xlsx")
        print(self.ugyfelek_df)
        '''
        except Exception as e:
            self.lbl_ugyfel_info.setText(f"⚠️ Ügyféllista hiba: {e}")
            return
        '''
        self.cmb_ugyfel.clear()
        self.cmb_ugyfel.addItem("— válassz ügyfelet —")
        for nev in self.ugyfelek_df["Név"].tolist():
            self.cmb_ugyfel.addItem(nev)

    def _ugyfel_changed(self):
        if self.ugyfelek_df is None or self.ugyfelek_df.empty:
            return

        nev = self.cmb_ugyfel.currentText().strip()
        if not nev or nev.startswith("—"):
            self.wiz.ugyfel = None
            self.lbl_ugyfel_info.setText("")
            return

        row = self.ugyfelek_df[self.ugyfelek_df["Név"] == nev]
        if row.empty:
            self.wiz.ugyfel = {"Név": nev}  # legalább a név meglegyen
            self.lbl_ugyfel_info.setText("")
            return

        rec = row.iloc[0].to_dict()
        self.wiz.ugyfel = rec  # <- ezt viszed tovább Step3-ba

        # opcionális: infó kiírás (ha vannak ilyen oszlopok)
        parts = []
        for col in ["Email", "Tel", "Város", "Lakcím", "Emelet, ajtó"]:
            if col in rec and str(rec[col]).strip():
                parts.append(f"{col}: {rec[col]}")
        self.lbl_ugyfel_info.setText("\n".join(parts))

    def run_calc(self):
        # 0) ügyfél ellenőrzés
        if getattr(self.wiz, "ugyfel", None) is None:
            Qw.QMessageBox.warning(self, "Hiányzik", "Előbb válassz ügyfelet!")
            return

        # 1) CSV tallózás
        csv_path, _ = Qw.QFileDialog.getOpenFileName(
            self, "Szabásjegyzék CSV kiválasztása", "",
            "CSV fájl (*.csv);;Minden fájl (*.*)"
        )
        if not csv_path:
            return

        # 2) a te jelenlegi logikád (ahogy írtad)
        # FONTOS: ha a te adatbeolvaso() maga tallóz, akkor a fenti QFileDialog nem kell.
        # Itt most átadjuk neki a csv_path-ot, ha tudod úgy módosítani.
        try:
            # ajánlott: a te adatbeolvaso fogadjon path-ot
            # self.df = self.wiz.arajanlatszerk.adatbeolvaso(csv_path)
            self.df = self.wiz.arajanlatszerk.adatbeolvaso()

            self.wiz.arajanlatszerk.szabjegyszerk.anyagigeny_szamitasa()
            anyagigeny_df = self.wiz.arajanlatszerk.szabjegyszerk.anyagigeny

        except Exception as e:
            Qw.QMessageBox.critical(self, "Hiba", f"Nem sikerült feldolgozni:\n{e}")
            return

        self.wiz.anyagigeny_df = anyagigeny_df
        self.wiz.nyomtathato_df = None

        self._show_preview(anyagigeny_df)
        self.btn_next.setEnabled(True)

    def _show_preview(self, df: pd.DataFrame):
        self.preview.setRowCount(min(len(df), 15))
        self.preview.setColumnCount(len(df.columns))
        self.preview.setHorizontalHeaderLabels([str(c) for c in df.columns])

        for r in range(min(len(df), 15)):
            for c, col in enumerate(df.columns):
                self.preview.setItem(r, c, Qw.QTableWidgetItem(str(df.iloc[r, c])))
        self.preview.resizeColumnsToContents()

class Step2MunkaAnyag(Qw.QGroupBox):
    def __init__(self, wiz):
        super().__init__("2. lépés – Munkamenet összeállítás és anyagok hozzárendelése")
        self.wiz = wiz
        lay = Qw.QVBoxLayout(self)

        self.info = Qw.QLabel(
            "Válassz munkafolyamatokat, és rögtön jelöld ki az érintett anyagokat az anyagigényből."
        )
        lay.addWidget(self.info)

        # -------- FELSŐ RÉSZ: munkafolyamat választó (VALÓDI) ----------
        # itt feltételezzük: wiz.munkadij_df már be van töltve (WizardWindow-ban)
        self.munka_widget = MunkafolyamatValasztoExcel()
        lay.addWidget(self.munka_widget)

        # ha hozzáad egy munkafolyamatot, rögtön vegyük át Step2-be:
        self.munka_widget.step_added.connect(self._on_step_added)

        # -------- ALSÓ RÉSZ: hozzárendelés ----------
        row = Qw.QHBoxLayout()
        lay.addLayout(row, 1)

        self.lst_steps = Qw.QListWidget()
        row.addWidget(self._box("Kiválasztott munkafolyamatok", self.lst_steps), 2)

        self.lst_anyag = Qw.QListWidget()
        self.lst_anyag.setSelectionMode(Qw.QAbstractItemView.NoSelection)
        row.addWidget(self._box("Érintett anyagok (anyagigényből)", self.lst_anyag), 3)

        # gombok
        btnrow = Qw.QHBoxLayout()
        self.btn_prev = Qw.QPushButton("← Vissza")
        self.btn_next = Qw.QPushButton("Tovább →")
        btnrow.addWidget(self.btn_prev)
        btnrow.addStretch(1)
        btnrow.addWidget(self.btn_next)
        lay.addLayout(btnrow)

        self.btn_prev.clicked.connect(lambda: self.wiz.goto(0))
        self.btn_next.clicked.connect(self._next)

        # esemény: ha másik munkalépésre kattintasz, frissítjük a pipákat
        self.lst_steps.currentTextChanged.connect(self._load_anyag_checks)

    def showEvent(self, e):
        super().showEvent(e)
        self._build_anyag_list()

        # ha már van korábbi állapot (pl. visszalépett), töltsük vissza
        self.lst_steps.clear()
        for step in self.wiz.munkalepesek:
            self.lst_steps.addItem(step["nev"])
        if self.lst_steps.count() > 0:
            self.lst_steps.setCurrentRow(0)

    def _box(self, title, widget):
        g = Qw.QGroupBox(title)
        l = Qw.QVBoxLayout(g)
        l.addWidget(widget)
        return g

    def _build_anyag_list(self):
        self.lst_anyag.clear()

        df = self.wiz.anyagigeny_df
        if df is None or df.empty:
            self.info.setText("⚠️ Nincs anyagigény. Menj vissza és számold ki előbb.")
            return

        # anyag oszlop
        anyag_col = "Anyag" if "Anyag" in df.columns else df.columns[0]
        anyagok = sorted(set(df[anyag_col].dropna().astype(str).tolist()))

        # jelzések duplázódásának elkerülése
        try:
            self.lst_anyag.itemChanged.disconnect()
        except Exception:
            pass

        for a in anyagok:
            item = Qw.QListWidgetItem(a)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.lst_anyag.addItem(item)

        self.lst_anyag.itemChanged.connect(self._on_anyag_changed)

    def _on_step_added(self, step: dict):
        """Ezt hívja a signal: amikor felül hozzáadsz egy munkafolyamatot."""
        nev = step.get("nev", "").strip()
        if not nev:
            return

        # munkalépések listája (wizard state)
        existing = {s["nev"] for s in self.wiz.munkalepesek}
        if nev not in existing:
            self.wiz.munkalepesek.append(step)

        # hozzárendelés dict inicializálása
        if nev not in self.wiz.hozzarendeles:
            self.wiz.hozzarendeles[nev] = []

        # listába felvétel, ha még nincs benne
        items = [self.lst_steps.item(i).text() for i in range(self.lst_steps.count())]
        if nev not in items:
            self.lst_steps.addItem(nev)
            self.lst_steps.setCurrentRow(self.lst_steps.count() - 1)  # ráállunk

    def _load_anyag_checks(self, munka_nev: str):
        if not munka_nev:
            return

        selected = set(self.wiz.hozzarendeles.get(munka_nev, []))

        self.lst_anyag.blockSignals(True)
        for i in range(self.lst_anyag.count()):
            it = self.lst_anyag.item(i)
            it.setCheckState(Qt.Checked if it.text() in selected else Qt.Unchecked)
        self.lst_anyag.blockSignals(False)

    def _on_anyag_changed(self, item: Qw.QListWidgetItem):
        munka_item = self.lst_steps.currentItem()
        if not munka_item:
            return
        munka = munka_item.text()

        cur = set(self.wiz.hozzarendeles.get(munka, []))
        if item.checkState() == Qt.Checked:
            cur.add(item.text())
        else:
            cur.discard(item.text())
        self.wiz.hozzarendeles[munka] = sorted(cur)

    def _next(self):
        if not self.wiz.munkalepesek:
            Qw.QMessageBox.warning(self, "Hiányzik", "Nem választottál munkafolyamatot.")
            return
        self.wiz.goto(2)


class Step3Export(Qw.QGroupBox):
    def __init__(self, wiz: WizardWindow):
        super().__init__("3. lépés – Árajánlat elkészítése")
        self.wiz = wiz
        lay = Qw.QVBoxLayout(self)

        self.lbl = Qw.QLabel("Kattints a generálásra. A program elkészíti a végleges árajánlatot.")
        lay.addWidget(self.lbl)

        self.btn_generate = Qw.QPushButton("Árajánlat generálása")
        lay.addWidget(self.btn_generate)

        self.btn_prev = Qw.QPushButton("← Vissza")
        lay.addWidget(self.btn_prev)

        self.btn_prev.clicked.connect(lambda: self.wiz.goto(1))
        self.btn_generate.clicked.connect(self.generate)

    def generate(self):
        # itt már megvan:
        # self.wiz.anyagigeny_df
        # self.wiz.hozzarendeles  (munkafolyamat -> anyagok)
        # + név mezők (ha kellenek, azt majd átadjuk)
        # ----
        """
        save_path, _ = Qw.QFileDialog.getSaveFileName(
            self, "Árajánlat mentése", "", "Excel fájl (*.xlsx)"
        )
        if not save_path:
            return

        # TODO: itt hívd a saját Arajanlat generálást:
        # araj.Arajanlat(...).elkeszites(save_path=save_path, ...)
        """
        self.wiz.arajanlatszerk.munkadijlepesek = self.wiz.munkalepesek
        self.wiz.arajanlatszerk.elkeszites()
        #Qw.QMessageBox.information(self, "Kész", f"Elmentve ide:\n{save_path}")

if __name__ == "__main__":
    app = Qw.QApplication([])
    w = WizardWindow()
    w.show()
    app.exec()