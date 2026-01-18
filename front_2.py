import os
import pandas as pd
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Qt

# ide importáld a saját moduljaidat:
# import app.arajanlat_keszito as araj
# import app.faj_beolvaso_kiirato as faj


class WizardWindow(Qw.QWidget):
    def __init__(self):
        super().__init__()
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

class Step1CsvImport(Qw.QGroupBox):
    def __init__(self, wiz: WizardWindow):
        super().__init__("1. lépés – CSV betallózás és anyagigény számítás")
        self.wiz = wiz
        lay = Qw.QVBoxLayout(self)

        self.lbl = Qw.QLabel("Válaszd ki a szabásjegyzék CSV fájlt, majd számoljuk az anyagigényt.")
        lay.addWidget(self.lbl)

        row = Qw.QHBoxLayout()
        self.path_edit = Qw.QLineEdit()
        self.path_edit.setPlaceholderText("CSV útvonal…")
        self.btn_browse = Qw.QPushButton("Tallózás…")
        row.addWidget(self.path_edit, 1)
        row.addWidget(self.btn_browse)
        lay.addLayout(row)

        self.btn_run = Qw.QPushButton("Anyagigény kiszámítása")
        lay.addWidget(self.btn_run)

        self.preview = Qw.QTableWidget()
        lay.addWidget(Qw.QLabel("Előnézet (anyagigény):"))
        lay.addWidget(self.preview, 1)

        self.btn_next = Qw.QPushButton("Tovább →")
        self.btn_next.setEnabled(False)
        lay.addWidget(self.btn_next)

        self.btn_browse.clicked.connect(self.browse_csv)
        self.btn_run.clicked.connect(self.run_calc)
        self.btn_next.clicked.connect(lambda: self.wiz.goto(1))

    def browse_csv(self):
        path, _ = Qw.QFileDialog.getOpenFileName(
            self, "Szabásjegyzék CSV kiválasztása", "",
            "CSV fájl (*.csv);;Minden fájl (*.*)"
        )
        if path:
            self.path_edit.setText(path)

    def run_calc(self):
        csv_path = self.path_edit.text().strip()
        if not csv_path or not os.path.exists(csv_path):
            Qw.QMessageBox.warning(self, "Hiba", "Érvénytelen CSV útvonal.")
            return

        self.wiz.csv_path = csv_path

        # -------------------------------
        # IDE KÖTÖD BE A SAJÁT LOGIKÁD:
        # 1) CSV beolvasás -> df
        # 2) szabásjegyzék szerkesztés
        # 3) anyagigény számítás -> anyagigeny_df
        #
        # Példa:
        # df = pd.read_csv(csv_path, encoding="utf-8", sep=";")  # vagy amilyen
        # szerk = SzabasjegyzekSzerkeszto(df)
        # anyagigeny_df, nyomtathato = szerk.anyagigeny_szamitasa()
        #
        # Most csak dummy:
        # -------------------------------
        try:
            df = pd.read_csv(csv_path, encoding="utf-8", sep=None, engine="python")
        except Exception as e:
            Qw.QMessageBox.critical(self, "CSV hiba", str(e))
            return

        # TODO: itt valós anyagigény számításod legyen:
        anyagigeny_df = df.head(10).copy()  # placeholder

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
    def __init__(self, wiz: WizardWindow):
        super().__init__("2. lépés – Munkamenet összeállítás és anyagok hozzárendelése")
        self.wiz = wiz
        lay = Qw.QVBoxLayout(self)

        self.info = Qw.QLabel("Válassz munkafolyamatokat, és rögtön jelöld ki az érintett anyagokat az anyagigényből.")
        lay.addWidget(self.info)

        # Felső rész: munkafolyamat választó (a meglévő widgetedet ide tedd!)
        self.munka_valaszto_placeholder = Qw.QLabel("IDE jön a MunkafolyamatValasztoExcel widget (adatbázisból)")
        self.munka_valaszto_placeholder.setStyleSheet("padding:8px; border:1px dashed #888;")
        lay.addWidget(self.munka_valaszto_placeholder)

        # Alsó rész: hozzárendelés
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
        """Amikor ez a lépés megjelenik, töltsük be az anyaglistát az anyagigényből."""
        super().showEvent(e)
        self._build_anyag_list()

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

        # itt állítsd be, hogy melyik oszlopból jön az anyagnév
        anyag_col = "Anyag" if "Anyag" in df.columns else df.columns[0]
        anyagok = sorted(set(df[anyag_col].dropna().astype(str).tolist()))

        for a in anyagok:
            item = Qw.QListWidgetItem(a)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.lst_anyag.addItem(item)

        self.lst_anyag.itemChanged.connect(self._on_anyag_changed)

    def add_munkalepes(self, nev: str):
        """Ezt hívd meg, amikor a munkafolyamat-választóból hozzáadsz egy lépést."""
        if not nev:
            return
        if nev not in self.wiz.hozzarendeles:
            self.wiz.hozzarendeles[nev] = []
            self.lst_steps.addItem(nev)
            self.lst_steps.setCurrentRow(self.lst_steps.count() - 1)  # ráállunk, hogy rögtön pipálhasson

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
        if not self.wiz.hozzarendeles:
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
        save_path, _ = Qw.QFileDialog.getSaveFileName(
            self, "Árajánlat mentése", "", "Excel fájl (*.xlsx)"
        )
        if not save_path:
            return

        # TODO: itt hívd a saját Arajanlat generálást:
        # araj.Arajanlat(...).elkeszites(save_path=save_path, ...)
        Qw.QMessageBox.information(self, "Kész", f"Elmentve ide:\n{save_path}")

