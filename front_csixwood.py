"""
CsixWood Árajánlat Varázsló — v7
Design: Windows 11 Fluent Light + CsixWood arany akcentus
Fix: nav gombok a WizardWindow globális nav_bar-jában (stack alatt)
"""

import math, os
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QLineEdit, QStackedWidget, QListWidget, QListWidgetItem,
    QFrame, QMessageBox, QSizePolicy, QHeaderView, QScrollArea,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette, QPixmap

import app.arajanlat_keszito as arajanlat
import app.faj_beolvaso_kiirato as faj

# ══════════════════════════════════════════════════════════════
#  PALETTA
# ══════════════════════════════════════════════════════════════
C = {
    "bg":          "#F3F3F3",
    "surface":     "#FFFFFF",
    "surface2":    "#F7F7F7",
    "hover":       "#F0F0F0",
    "pressed":     "#E8E8E8",
    "text":        "#1A1A1A",
    "text2":       "#5A5A5A",
    "text3":       "#9A9A9A",
    "border":      "#E0E0E0",
    "border2":     "#C8C8C8",
    "divider":     "#EBEBEB",
    "gold":        "#C8902A",
    "gold_lt":     "#D9A040",
    "gold_dk":     "#A87020",
    "gold_bg":     "#FDF4E7",
    "gold_border": "#E8C070",
    "ok":          "#107C10",
    "err":         "#C42B1C",
}

# ══════════════════════════════════════════════════════════════
#  STYLESHEET
# ══════════════════════════════════════════════════════════════
QSS = f"""
* {{ font-family:'Segoe UI',system-ui,sans-serif; font-size:13px; border:none; outline:none; margin:0; padding:0; }}
QWidget {{ background:{C['bg']}; color:{C['text']}; }}
QWidget#Header  {{ background:{C['surface']}; border-bottom:1px solid {C['border']}; }}
QWidget#StepBar {{ background:{C['surface']}; border-bottom:1px solid {C['border']}; }}
QWidget#NavBar  {{ background:{C['surface']}; border-top:1px solid {C['border']}; }}
QWidget#Footer  {{ background:{C['surface']}; border-top:1px solid {C['border']}; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background:{C['bg']}; border:none; }}
QFrame#Card {{ background:{C['surface']}; border:1px solid {C['border']}; border-radius:8px; }}
QFrame#Sep  {{ background:{C['divider']}; min-height:1px; max-height:1px; border:none; }}

QPushButton {{
    background:{C['gold']}; color:#fff; border:none; border-radius:4px;
    padding:0 20px; font-size:13px; font-weight:600; min-height:36px;
}}
QPushButton:hover   {{ background:{C['gold_lt']}; }}
QPushButton:pressed {{ background:{C['gold_dk']}; }}
QPushButton:disabled {{ background:{C['hover']}; color:{C['text3']}; }}
QPushButton#BtnGhost {{
    background:transparent; color:{C['text2']};
    border:1px solid {C['border2']}; border-radius:4px;
}}
QPushButton#BtnGhost:hover   {{ background:{C['hover']}; color:{C['text']}; }}
QPushButton#BtnGhost:pressed {{ background:{C['pressed']}; }}
QPushButton#BtnIcon {{
    background:{C['surface']}; color:{C['text2']};
    border:1px solid {C['border']}; border-radius:4px;
    font-size:15px;
    min-width:34px; max-width:34px; min-height:34px; max-height:34px; padding:0;
}}
QPushButton#BtnIcon:hover {{ background:{C['hover']}; color:{C['gold']}; border-color:{C['gold_border']}; }}

QLineEdit, QComboBox {{
    background:{C['surface']}; border:1px solid {C['border2']}; border-radius:4px;
    padding:0 10px; color:{C['text']}; min-height:34px; selection-background-color:{C['gold_bg']};
}}
QLineEdit:focus, QComboBox:focus {{ border-color:{C['gold']}; }}
QLineEdit:hover:!focus, QComboBox:hover:!focus {{ background:{C['hover']}; }}
QComboBox::drop-down {{ border:none; width:30px; }}
QComboBox::down-arrow {{ border-left:4px solid transparent; border-right:4px solid transparent; border-top:5px solid {C['text2']}; margin-right:10px; }}
QComboBox QAbstractItemView {{
    background:{C['surface']}; border:1px solid {C['border']}; border-radius:4px;
    color:{C['text']}; selection-background-color:{C['gold_bg']}; outline:none; padding:4px;
}}
QComboBox QAbstractItemView::item {{ min-height:32px; padding:0 8px; border-radius:3px; }}
QComboBox QAbstractItemView::item:hover {{ background:{C['hover']}; }}

QTableWidget {{
    background:{C['surface']}; alternate-background-color:{C['surface2']};
    border:1px solid {C['border']}; border-radius:6px; color:{C['text']};
    font-size:12px; gridline-color:{C['divider']}; outline:none;
}}
QTableWidget::item {{ padding:0 10px; min-height:32px; border:none; }}
QTableWidget::item:selected {{ background:{C['gold_bg']}; color:{C['text']}; }}
QHeaderView {{ background:{C['surface2']}; }}
QHeaderView::section {{
    background:{C['surface2']}; color:{C['text2']}; border:none;
    border-bottom:1px solid {C['border']}; border-right:1px solid {C['divider']};
    padding:0 10px; height:32px; font-size:11px; font-weight:600;
}}
QHeaderView::section:last-child {{ border-right:none; }}

QListWidget {{
    background:{C['surface']}; border:1px solid {C['border']}; border-radius:6px;
    color:{C['text']}; outline:none;
}}
QListWidget::item {{ padding:0 12px; min-height:36px; border-bottom:1px solid {C['divider']}; }}
QListWidget::item:last-child {{ border-bottom:none; }}
QListWidget::item:selected {{ background:{C['gold_bg']}; color:{C['text']}; border-left:2px solid {C['gold']}; }}
QListWidget::item:hover:!selected {{ background:{C['hover']}; }}

QScrollBar:vertical {{ background:transparent; width:6px; margin:2px; border-radius:3px; }}
QScrollBar::handle:vertical {{ background:{C['border2']}; border-radius:3px; min-height:20px; }}
QScrollBar::handle:vertical:hover {{ background:{C['text3']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
QScrollBar:horizontal {{ background:transparent; height:6px; margin:2px; border-radius:3px; }}
QScrollBar::handle:horizontal {{ background:{C['border2']}; border-radius:3px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width:0; }}

QGroupBox {{
    background:{C['surface']}; border:1px solid {C['border']}; border-radius:6px;
    margin-top:8px; padding:10px; font-size:10px; font-weight:600; color:{C['text2']};
}}
QGroupBox::title {{
    subcontrol-origin:margin; subcontrol-position:top left; left:10px; top:-6px;
    padding:1px 8px; background:{C['surface']}; color:{C['text2']};
    font-size:10px; font-weight:600;
}}
"""

# ══════════════════════════════════════════════════════════════
#  SEGÉDEK
# ══════════════════════════════════════════════════════════════
def sep_line():
    f = QFrame(); f.setObjectName("Sep"); f.setFrameShape(QFrame.HLine); return f

def make_card():
    f = QFrame(); f.setObjectName("Card"); return f

def make_table():
    t = QTableWidget()
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setSelectionMode(QAbstractItemView.SingleSelection)
    t.verticalHeader().setVisible(False)
    t.setAlternatingRowColors(True)
    t.setShowGrid(True)
    t.horizontalHeader().setStretchLastSection(True)
    t.verticalHeader().setDefaultSectionSize(32)
    return t

def page_title(text):
    l = QLabel(text)
    l.setStyleSheet(f"font-size:20px;font-weight:700;color:{C['text']};background:transparent;")
    return l

def page_sub(text):
    l = QLabel(text); l.setWordWrap(True)
    l.setStyleSheet(f"font-size:13px;color:{C['text2']};background:transparent;")
    return l

def section_tag(text):
    l = QLabel(text)
    l.setStyleSheet(f"font-size:11px;font-weight:600;color:{C['text2']};background:transparent;")
    return l

def gold_tag(text):
    l = QLabel(text)
    l.setStyleSheet(f"background:{C['gold_bg']};color:{C['gold']};border:1px solid {C['gold_border']};border-radius:3px;padding:1px 8px;font-size:11px;font-weight:600;")
    return l

def info_row(html=""):
    l = QLabel(html); l.setTextFormat(Qt.RichText); l.setWordWrap(True)
    l.setStyleSheet(f"background:{C['gold_bg']};border-left:2px solid {C['gold']};border-radius:0 4px 4px 0;padding:8px 12px;color:{C['text2']};font-size:12px;")
    return l

def card_header(title):
    w = QWidget()
    w.setStyleSheet(f"background:{C['surface2']};border-radius:7px 7px 0 0;")
    lay = QHBoxLayout(w); lay.setContentsMargins(16,10,16,10)
    lay.addWidget(section_tag(title)); lay.addStretch()
    return w

def make_scroll_inner():
    """Scrollozható belső widget. Visszaad: (scroll_widget, content_layout)"""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setStyleSheet(f"background:{C['bg']};border:none;")
    inner = QWidget(); inner.setStyleSheet(f"background:{C['bg']};")
    lay = QVBoxLayout(inner); lay.setContentsMargins(28,24,28,24); lay.setSpacing(16)
    scroll.setWidget(inner)
    return scroll, lay

# ══════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════
class HeaderBar(QWidget):
    def __init__(self, logo_path=None):
        super().__init__(); self.setObjectName("Header"); self.setFixedHeight(56)
        lay = QHBoxLayout(self); lay.setContentsMargins(16,0,20,0); lay.setSpacing(12)

        if logo_path and os.path.exists(logo_path):
            lbl = QLabel(); pix = QPixmap(logo_path).scaledToHeight(40, Qt.SmoothTransformation)
            lbl.setPixmap(pix); lbl.setStyleSheet("background:transparent;"); lay.addWidget(lbl)
        else:
            c = QLabel("CW"); c.setFixedSize(40,40); c.setAlignment(Qt.AlignCenter)
            c.setStyleSheet(f"background:#1C1008;color:{C['gold']};border-radius:20px;font-size:14px;font-weight:800;")
            lay.addWidget(c)

        vl = QFrame(); vl.setFrameShape(QFrame.VLine); vl.setFixedSize(1,28)
        vl.setStyleSheet(f"background:{C['border']};border:none;"); lay.addWidget(vl)

        n = QLabel("CsixWood")
        n.setStyleSheet(f"font-size:15px;font-weight:700;color:{C['text']};background:transparent;")
        lay.addWidget(n)
        s = QLabel("Árajánlat rendszer")
        s.setStyleSheet(f"font-size:12px;color:{C['text3']};background:transparent;")
        lay.addWidget(s)
        lay.addStretch()
        lay.addWidget(gold_tag("CsixWood"))

# ══════════════════════════════════════════════════════════════
#  STEP BAR
# ══════════════════════════════════════════════════════════════
class StepBar(QWidget):
    STEPS = ["1  Ügyfél & CSV", "2  Munkafolyamatok", "3  Generálás"]

    def __init__(self):
        super().__init__(); self.setObjectName("StepBar"); self.setFixedHeight(40); self.current = 0
        lay = QHBoxLayout(self); lay.setContentsMargins(16,4,16,4); lay.setSpacing(4)
        self.btns = []
        for i, name in enumerate(self.STEPS):
            b = QLabel(name); b.setAlignment(Qt.AlignCenter)
            b.setFixedHeight(28); b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            lay.addWidget(b); self.btns.append(b)
            if i < len(self.STEPS)-1:
                a = QLabel("›"); a.setFixedWidth(20); a.setAlignment(Qt.AlignCenter)
                a.setStyleSheet(f"color:{C['border2']};font-size:16px;background:transparent;")
                lay.addWidget(a)
        self._refresh()

    def set_step(self, idx):
        self.current = idx; self._refresh()

    def _refresh(self):
        for i, b in enumerate(self.btns):
            if i < self.current:
                b.setText(f"✓  {self.STEPS[i][3:]}")
                b.setStyleSheet(f"color:{C['ok']};font-size:12px;font-weight:600;background:transparent;border-radius:4px;")
            elif i == self.current:
                b.setText(self.STEPS[i])
                b.setStyleSheet(f"color:{C['gold']};font-size:12px;font-weight:700;background:{C['gold_bg']};border-radius:4px;border:1px solid {C['gold_border']};padding:0 8px;")
            else:
                b.setText(self.STEPS[i])
                b.setStyleSheet(f"color:{C['text3']};font-size:12px;background:transparent;border-radius:4px;")

# ══════════════════════════════════════════════════════════════
#  MUNKAFOLYAMAT VÁLASZTÓ
# ══════════════════════════════════════════════════════════════
class MunkaValaszto(QWidget):
    step_added = Signal(dict)

    def __init__(self):
        super().__init__(); self.setStyleSheet("background:transparent;")
        link = "https://1drv.ms/x/c/595ECD328626FCDE/IQBQc2FuUwOMRp7xoE1-idfeAb-lcS22MI8C1r-XFIJB5cE?e=JHUQ2u"
        try:
            df = faj.BeolvasKiirat().excel_beolvas_onedrive_linkbol(megosztasi_link=link, cel_mappa="data", fajlnev="munkadij.xlsx")
            self.df = df.reset_index(drop=True)
        except:
            self.df = pd.DataFrame(columns=["nev","leiras","szamtip","ar"])

        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(8)
        self.search = QLineEdit(); self.search.setPlaceholderText("Keresés…"); root.addWidget(self.search)

        tables = QHBoxLayout(); tables.setSpacing(8)

        def make_side(title):
            f = QFrame(); f.setObjectName("Card")
            lay = QVBoxLayout(f); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
            lay.addWidget(card_header(title)); lay.addWidget(sep_line())
            tbl = make_table(); tbl.setColumnCount(4)
            tbl.setHorizontalHeaderLabels(["Név","Leírás","Típus","Ár"])
            tbl.setStyleSheet("border:none;border-radius:0 0 6px 6px;")
            lay.addWidget(tbl)
            return f, tbl

        lf, self.tbl_r = make_side("Elérhető munkák"); tables.addWidget(lf, 4)

        bc = QVBoxLayout(); bc.setAlignment(Qt.AlignCenter); bc.setSpacing(4)
        for attr, sym, tip in [("btn_add","→","Hozzáadás"),("btn_rem","←","Törlés"),("btn_up","↑","Feljebb"),("btn_dn","↓","Lejjebb")]:
            b = QPushButton(sym); b.setObjectName("BtnIcon"); b.setToolTip(tip); setattr(self, attr, b)
            if sym == "↑": bc.addSpacing(6)
            bc.addWidget(b)
        tables.addLayout(bc)

        rf, self.tbl_s = make_side("Kiválasztott munkák"); tables.addWidget(rf, 4)
        root.addLayout(tables)

        self.search.textChanged.connect(self._refresh)
        self.btn_add.clicked.connect(self._add)
        self.btn_rem.clicked.connect(self._rem)
        self.btn_up.clicked.connect(lambda: self._move(-1))
        self.btn_dn.clicked.connect(lambda: self._move(1))
        self.tbl_r.cellDoubleClicked.connect(lambda *_: self._add())
        self._refresh()

    def _s(self, x):
        if x is None: return ""
        try:
            if pd.isna(x): return ""
        except: pass
        return str(x)

    def _refresh(self):
        txt = self.search.text().strip().lower()
        df = self.df if not txt else self.df[
            self.df["nev"].str.lower().str.contains(txt, na=False) |
            self.df["leiras"].str.lower().str.contains(txt, na=False)]
        self.tbl_r.setRowCount(len(df))
        for r, (_, row) in enumerate(df.iterrows()):
            for c, k in enumerate(["nev","leiras","szamtip"]):
                self.tbl_r.setItem(r, c, QTableWidgetItem(self._s(row.get(k,""))))
            try: ar = int(float(row.get("ar",0) or 0))
            except: ar = 0
            it = QTableWidgetItem(f"{ar:,} Ft".replace(",","\u202f"))
            it.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
            self.tbl_r.setItem(r, 3, it)
        self.tbl_r.resizeColumnsToContents()

    def _key(self, i): return tuple(self.tbl_s.item(i,c).text() for c in range(3))

    def _add(self):
        r = self.tbl_r.currentRow()
        if r < 0: return
        vals = [self.tbl_r.item(r,c).text() for c in range(4)]
        if tuple(vals[:3]) in {self._key(i) for i in range(self.tbl_s.rowCount())}: return
        nr = self.tbl_s.rowCount(); self.tbl_s.insertRow(nr)
        for c, v in enumerate(vals[:3]): self.tbl_s.setItem(nr,c,QTableWidgetItem(v))
        it = QTableWidgetItem(vals[3]); it.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.tbl_s.setItem(nr,3,it); self.tbl_s.resizeColumnsToContents()
        ar_c = vals[3].replace("\u202f","").replace(" ","").replace("Ft","")
        self.step_added.emit({"nev":vals[0],"leiras":vals[1],"szamtip":vals[2],"ar":int(ar_c) if ar_c.isdigit() else 0})

    def _rem(self):
        r = self.tbl_s.currentRow()
        if r >= 0: self.tbl_s.removeRow(r)

    def _move(self, d):
        r = self.tbl_s.currentRow()
        if r < 0: return
        nr = r + d
        if nr < 0 or nr >= self.tbl_s.rowCount(): return
        for c in range(4):
            a, b = self.tbl_s.takeItem(r,c), self.tbl_s.takeItem(nr,c)
            self.tbl_s.setItem(r,c,b); self.tbl_s.setItem(nr,c,a)
        self.tbl_s.setCurrentCell(nr, 0)

    def get_selected(self):
        out = []
        for i in range(self.tbl_s.rowCount()):
            ar_raw = self.tbl_s.item(i,3).text() if self.tbl_s.item(i,3) else "0"
            ar_c = ar_raw.replace("\u202f","").replace(" ","").replace("Ft","")
            out.append({"nev":self.tbl_s.item(i,0).text(),"leiras":self.tbl_s.item(i,1).text(),
                        "szamtip":self.tbl_s.item(i,2).text(),"ar":int(ar_c) if ar_c.isdigit() else 0})
        return out

# ══════════════════════════════════════════════════════════════
#  1. LÉPÉS
# ══════════════════════════════════════════════════════════════
class Step1(QWidget):
    btn_load_ready = Signal()   # tüzel amikor CSV betöltve, engedélyezi a Továbbot

    def __init__(self, wiz):
        super().__init__(); self.wiz = wiz; self.ugyfelek_df = None
        self.setStyleSheet(f"background:{C['bg']};")
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        scroll, lay = make_scroll_inner()
        root.addWidget(scroll)

        lay.addWidget(page_title("Ügyfél és szabásjegyzék"))
        lay.addWidget(page_sub("Válaszd ki az ügyfelet, majd töltsd be a szabásztervező által exportált CSV fájlt."))
        lay.addWidget(sep_line())

        # Ügyfél kártya
        ug = make_card(); ul = QVBoxLayout(ug); ul.setContentsMargins(0,0,0,0); ul.setSpacing(0)
        ul.addWidget(card_header("Ügyfél kiválasztása")); ul.addWidget(sep_line())
        ub = QWidget(); ub.setStyleSheet(f"background:{C['surface']};")
        ub_l = QVBoxLayout(ub); ub_l.setContentsMargins(16,14,16,14); ub_l.setSpacing(10)
        self.cmb = QComboBox(); self.cmb.setEditable(True); self.cmb.setInsertPolicy(QComboBox.NoInsert)
        self.cmb.setPlaceholderText("Keresés névben…"); ub_l.addWidget(self.cmb)
        self.lbl_info = info_row(); self.lbl_info.setVisible(False); ub_l.addWidget(self.lbl_info)
        ul.addWidget(ub); lay.addWidget(ug)

        # CSV kártya
        cg = make_card(); cl = QVBoxLayout(cg); cl.setContentsMargins(0,0,0,0); cl.setSpacing(0)
        cl.addWidget(card_header("Szabásjegyzék betöltése")); cl.addWidget(sep_line())
        cb = QWidget(); cb.setStyleSheet(f"background:{C['surface']};")
        cb_l = QVBoxLayout(cb); cb_l.setContentsMargins(16,14,16,14); cb_l.setSpacing(12)

        btn_row = QHBoxLayout()
        self.btn_load = QPushButton("  Fájl megnyitása és számítás")
        self.btn_load.setObjectName("BtnGhost"); self.btn_load.setMinimumWidth(260); btn_row.addWidget(self.btn_load); btn_row.addStretch()
        self.lbl_st = QLabel("Válassz CSV fájlt a számításhoz.")
        self.lbl_st.setStyleSheet(f"color:{C['text3']};font-size:12px;background:transparent;")
        btn_row.addWidget(self.lbl_st); cb_l.addLayout(btn_row)

        cb_l.addWidget(sep_line()); cb_l.addWidget(section_tag("Anyagigény előnézet"))
        self.preview = make_table(); self.preview.setMinimumHeight(220); cb_l.addWidget(self.preview)
        cl.addWidget(cb); lay.addWidget(cg, 1)

        self.btn_load.clicked.connect(self._run)
        self._load_ugyfelek()
        self.cmb.currentIndexChanged.connect(self._ugyfel_changed)

    def _load_ugyfelek(self):
        link = "https://1drv.ms/x/c/595ECD328626FCDE/IQCAAzRsxtjJRJhSfNq79RZ8AWpcUCbT_AV30IeTavTymUc?e=lrUfMC"
        try:
            self.ugyfelek_df = self.wiz.faj.excel_beolvas_onedrive_linkbol(megosztasi_link=link, cel_mappa="data", fajlnev="ugyfelek_adat.xlsx")
        except: self.ugyfelek_df = pd.DataFrame(columns=["Név"])
        self.cmb.clear(); self.cmb.addItem("— válassz ügyfelet —")
        for nev in self.ugyfelek_df["Név"].tolist(): self.cmb.addItem(str(nev))

    def _ugyfel_changed(self):
        if self.ugyfelek_df is None: return
        nev = self.cmb.currentText().strip()
        if not nev or nev.startswith("—"):
            self.wiz.ugyfel = None; self.lbl_info.setVisible(False); return
        row = self.ugyfelek_df[self.ugyfelek_df["Név"] == nev]
        if row.empty:
            self.wiz.ugyfel = {"Név": nev}; self.lbl_info.setVisible(False); return
        rec = row.iloc[0].to_dict()
        self.wiz.ugyfel = rec; self.wiz.arajanlatszerk.ugyfel = rec
        parts = []
        for col in ["Email","Tel","Város","Lakcím","Emelet, ajtó"]:
            if col not in rec: continue
            val = rec[col]
            if val is None or (isinstance(val, float) and math.isnan(val)): continue
            if col == "Tel":
                val = self.wiz.arajanlatszerk.telefonszam_formazo(val)
                if not val: continue
            if str(val).strip():
                parts.append(f"<b style='color:{C['text']};'>{col}:</b> {val}")
        if parts:
            self.lbl_info.setText("&nbsp;&nbsp;·&nbsp;&nbsp;".join(parts))
            self.lbl_info.setVisible(True)

    def _run(self):
        if not getattr(self.wiz, "ugyfel", None):
            QMessageBox.warning(self, "Hiányzó", "Előbb válassz ügyfelet!"); return
        self.lbl_st.setText("Feldolgozás…")
        self.lbl_st.setStyleSheet(f"color:{C['text2']};font-style:italic;font-size:12px;background:transparent;")
        QApplication.processEvents()
        try:
            self.wiz.arajanlatszerk.adatbeolvaso()
            self.wiz.arajanlatszerk.szabjegyszerk.anyagigeny_szamitasa()
            df = self.wiz.arajanlatszerk.szabjegyszerk.anyagigeny
        except Exception as e:
            QMessageBox.critical(self, "Hiba", str(e))
            self.lbl_st.setText("Hiba.")
            self.lbl_st.setStyleSheet(f"color:{C['err']};font-size:12px;background:transparent;"); return
        self.wiz.anyagigeny_df = df
        self.lbl_st.setText(f"✓  {len(df)} anyagféle feldolgozva")
        self.lbl_st.setStyleSheet(f"color:{C['ok']};font-weight:600;font-size:12px;background:transparent;")
        cols = list(df.columns)
        self.preview.setColumnCount(len(cols)); self.preview.setHorizontalHeaderLabels(cols)
        self.preview.setRowCount(len(df))
        self.preview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        for r in range(len(df)):
            for c, col in enumerate(cols):
                v = df.iloc[r,c]
                self.preview.setItem(r,c,QTableWidgetItem(str(round(v,3) if isinstance(v,float) else v)))
        self.btn_load_ready.emit()

# ══════════════════════════════════════════════════════════════
#  2. LÉPÉS
# ══════════════════════════════════════════════════════════════
class Step2(QWidget):
    def __init__(self, wiz):
        super().__init__(); self.wiz = wiz
        self.setStyleSheet(f"background:{C['bg']};")
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        scroll, lay = make_scroll_inner()
        root.addWidget(scroll)

        lay.addWidget(page_title("Munkafolyamatok"))
        lay.addWidget(page_sub("Válaszd ki a munkadíj lépéseket, majd rendeld hozzá az érintett anyagokat."))
        lay.addWidget(sep_line())

        # Munkadíj kártya
        mk = make_card(); ml = QVBoxLayout(mk); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)
        ml.addWidget(card_header("Munkadíj adatbázis")); ml.addWidget(sep_line())
        mb = QWidget(); mb.setStyleSheet(f"background:{C['surface']};")
        mb_l = QVBoxLayout(mb); mb_l.setContentsMargins(14,12,14,14)
        self.munka = MunkaValaszto(); self.munka.setMinimumHeight(280); mb_l.addWidget(self.munka)
        ml.addWidget(mb); lay.addWidget(mk, 2)
        self.munka.step_added.connect(self._on_step_added)

        # Hozzárendelés kártya
        ha = make_card(); ha_l = QVBoxLayout(ha); ha_l.setContentsMargins(0,0,0,0); ha_l.setSpacing(0)
        ha_l.addWidget(card_header("Anyag hozzárendelés")); ha_l.addWidget(sep_line())
        hab = QWidget(); hab.setStyleSheet(f"background:{C['surface']};")
        hab_l = QHBoxLayout(hab); hab_l.setContentsMargins(14,12,14,14); hab_l.setSpacing(14)

        lw = QVBoxLayout(); lw.setSpacing(6); lw.addWidget(section_tag("Kiválasztott lépések"))
        self.lst_steps = QListWidget(); self.lst_steps.setMaximumWidth(260); self.lst_steps.setMinimumHeight(180)
        lw.addWidget(self.lst_steps); hab_l.addLayout(lw)

        rw = QVBoxLayout(); rw.setSpacing(6); rw.addWidget(section_tag("Érintett anyagok (pipáld be)"))
        self.lst_anyag = QListWidget(); self.lst_anyag.setSelectionMode(QAbstractItemView.NoSelection)
        self.lst_anyag.setMinimumHeight(180); rw.addWidget(self.lst_anyag); hab_l.addLayout(rw,1)
        ha_l.addWidget(hab); lay.addWidget(ha,1)

        self.lst_steps.currentTextChanged.connect(self._load_checks)

    def showEvent(self, e):
        super().showEvent(e); self._build_anyag()
        self.lst_steps.clear()
        for s in self.wiz.munkalepesek: self.lst_steps.addItem(s["nev"])
        if self.lst_steps.count(): self.lst_steps.setCurrentRow(0)

    def _build_anyag(self):
        self.lst_anyag.clear()
        df = self.wiz.anyagigeny_df
        if df is None or df.empty: return
        col = "Anyag" if "Anyag" in df.columns else df.columns[0]
        try: self.lst_anyag.itemChanged.disconnect()
        except: pass
        for a in sorted(set(df[col].dropna().astype(str))):
            it = QListWidgetItem(a); it.setFlags(it.flags()|Qt.ItemIsUserCheckable); it.setCheckState(Qt.Unchecked)
            self.lst_anyag.addItem(it)
        self.lst_anyag.itemChanged.connect(self._on_anyag)

    def _on_step_added(self, step):
        nev = step.get("nev","").strip()
        if not nev: return
        if nev not in {s["nev"] for s in self.wiz.munkalepesek}: self.wiz.munkalepesek.append(step)
        if nev not in self.wiz.hozzarendeles: self.wiz.hozzarendeles[nev] = []
        items = [self.lst_steps.item(i).text() for i in range(self.lst_steps.count())]
        if nev not in items:
            self.lst_steps.addItem(nev); self.lst_steps.setCurrentRow(self.lst_steps.count()-1)

    def _load_checks(self, munka):
        if not munka: return
        sel = set(self.wiz.hozzarendeles.get(munka,[]))
        self.lst_anyag.blockSignals(True)
        for i in range(self.lst_anyag.count()):
            it = self.lst_anyag.item(i); it.setCheckState(Qt.Checked if it.text() in sel else Qt.Unchecked)
        self.lst_anyag.blockSignals(False)

    def _on_anyag(self, item):
        mi = self.lst_steps.currentItem()
        if not mi: return
        cur = set(self.wiz.hozzarendeles.get(mi.text(),[]))
        if item.checkState() == Qt.Checked: cur.add(item.text())
        else: cur.discard(item.text())
        self.wiz.hozzarendeles[mi.text()] = sorted(cur)

    def _next(self):
        if not self.wiz.munkalepesek:
            QMessageBox.warning(self,"Hiányzó","Nem választottál munkafolyamatot!"); return
        self.wiz.goto(2)

# ══════════════════════════════════════════════════════════════
#  3. LÉPÉS
# ══════════════════════════════════════════════════════════════
class Step3(QWidget):
    def __init__(self, wiz):
        super().__init__(); self.wiz = wiz
        self.setStyleSheet(f"background:{C['bg']};")
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        scroll, lay = make_scroll_inner()
        root.addWidget(scroll)

        lay.addWidget(page_title("Árajánlat generálása"))
        lay.addWidget(page_sub("Minden adat összegyűlt. Az Excel fájl az ügyfél mappájába kerül."))
        lay.addWidget(sep_line())

        # Összefoglaló kártya
        sg = make_card(); sl = QVBoxLayout(sg); sl.setContentsMargins(0,0,0,0); sl.setSpacing(0)
        sl.addWidget(card_header("Összefoglalás")); sl.addWidget(sep_line())
        sb = QWidget(); sb.setStyleSheet(f"background:{C['surface']};")
        sb_l = QVBoxLayout(sb); sb_l.setContentsMargins(16,14,16,14); sb_l.setSpacing(8)
        self.sum_rows = []
        for key in ["Ügyfél","Anyagfélék","Munkafolyamatok"]:
            rw = QWidget(); rw.setStyleSheet(f"background:{C['surface2']};border-radius:4px;")
            rl = QHBoxLayout(rw); rl.setContentsMargins(12,10,12,10)
            kl = QLabel(key); kl.setStyleSheet(f"color:{C['text2']};font-size:12px;font-weight:600;background:transparent;")
            vl = QLabel("—"); vl.setStyleSheet(f"color:{C['text']};font-size:12px;background:transparent;")
            rl.addWidget(kl); rl.addStretch(); rl.addWidget(vl)
            sb_l.addWidget(rw); self.sum_rows.append(vl)
        sl.addWidget(sb); lay.addWidget(sg)

        self.lbl_res = QLabel(); self.lbl_res.setAlignment(Qt.AlignCenter); self.lbl_res.setWordWrap(True)
        self.lbl_res.setMinimumHeight(30); self.lbl_res.setStyleSheet("background:transparent;font-size:13px;")
        lay.addWidget(self.lbl_res)
        lay.addStretch()

        self.btn_gen_clicked = self._gen   # WizardWindow hívja

    def showEvent(self, e):
        super().showEvent(e)
        ugyfel = getattr(self.wiz,"ugyfel",None) or {}
        nev = ugyfel.get("Név","—"); varos = ugyfel.get("Város","")
        na = len(self.wiz.anyagigeny_df) if self.wiz.anyagigeny_df is not None else 0
        nm = len(self.wiz.munkalepesek)
        for lbl, val in zip(self.sum_rows, [nev+(f", {varos}" if varos else ""), f"{na} db", f"{nm} db"]):
            lbl.setText(val)

    def _gen(self):
        self.lbl_res.setText("Feldolgozás folyamatban…")
        self.lbl_res.setStyleSheet(f"color:{C['text2']};font-style:italic;background:transparent;")
        self.wiz.btn_fwd3.setEnabled(False)
        QApplication.processEvents()
        try:
            self.wiz.arajanlatszerk.munkadijlepesek      = self.wiz.munkalepesek
            self.wiz.arajanlatszerk.munkad_erintettanyag = self.wiz.hozzarendeles
            self.wiz.arajanlatszerk.elkeszites()
            self.lbl_res.setText("✓  Az árajánlat sikeresen elkészült!")
            self.lbl_res.setStyleSheet(f"color:{C['ok']};font-weight:700;font-size:13px;background:transparent;")
        except Exception as e:
            self.lbl_res.setText(f"Hiba: {e}")
            self.lbl_res.setStyleSheet(f"color:{C['err']};font-size:12px;background:transparent;")
        finally:
            self.wiz.btn_fwd3.setEnabled(True)

# ══════════════════════════════════════════════════════════════
#  FŐ ABLAK
# ══════════════════════════════════════════════════════════════
class WizardWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.faj            = faj.BeolvasKiirat()
        self.arajanlatszerk = arajanlat.Arajanlat()
        self.ugyfel         = None
        self.anyagigeny_df  = None
        self.munkalepesek   = []
        self.hozzarendeles  = {}

        self.setWindowTitle("CsixWood – Árajánlat")
        self.setMinimumSize(1100, 760)
        self.setStyleSheet(f"background:{C['bg']};")

        root = QVBoxLayout(self)
        root.setContentsMargins(0,0,0,0)
        root.setSpacing(0)

        LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/logo.PNG")
        root.addWidget(HeaderBar(logo_path=LOGO))

        self.stepbar = StepBar()
        root.addWidget(self.stepbar)

        # Stack — stretch=1
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background:{C['bg']};")
        self.p1 = Step1(self)
        self.p2 = Step2(self)
        self.p3 = Step3(self)
        for p in [self.p1, self.p2, self.p3]:
            self.stack.addWidget(p)
        root.addWidget(self.stack, 1)

        # ── Nav bar — ALL gombok itt születnek, show/hide váltás ──
        nav_bar = QWidget()
        nav_bar.setObjectName("NavBar")
        nav_bar.setFixedHeight(60)
        nav_bar.setStyleSheet(f"background:{C['surface']};border-top:1px solid {C['border']};")
        nav_lay = QHBoxLayout(nav_bar)
        nav_lay.setContentsMargins(28, 0, 28, 0)
        nav_lay.setSpacing(12)

        # Vissza gombok (bal oldal)
        self.btn_back1 = QPushButton("‹  Vissza")   # oldal 1 → nincs vissza, hidden
        self.btn_back2 = QPushButton("‹  Vissza")   # oldal 2 → 1-re
        self.btn_back3 = QPushButton("‹  Vissza")   # oldal 3 → 2-re
        for b in [self.btn_back1, self.btn_back2, self.btn_back3]:
            b.setObjectName("BtnGhost")
            b.setMinimumWidth(120)
            b.setMinimumHeight(36)
            nav_lay.addWidget(b)

        nav_lay.addStretch(1)

        # Előre / akció gombok (jobb oldal)
        self.btn_fwd1 = QPushButton("Tovább  ›")              # oldal 1
        self.btn_fwd2 = QPushButton("Generálás  ›")           # oldal 2
        self.btn_fwd3 = QPushButton("  Árajánlat elkészítése") # oldal 3
        self.btn_fwd1.setObjectName("BtnGhost"); self.btn_fwd1.setMinimumWidth(140); self.btn_fwd1.setMinimumHeight(36)
        self.btn_fwd2.setObjectName("BtnGhost"); self.btn_fwd2.setMinimumWidth(160); self.btn_fwd2.setMinimumHeight(36)
        self.btn_fwd3.setObjectName("BtnGhost"); self.btn_fwd3.setMinimumWidth(220); self.btn_fwd3.setMinimumHeight(36)
        for b in [self.btn_fwd1, self.btn_fwd2, self.btn_fwd3]:
            nav_lay.addWidget(b)

        root.addWidget(nav_bar)

        # Footer
        footer = QWidget(); footer.setObjectName("Footer"); footer.setFixedHeight(24)
        fl = QHBoxLayout(footer); fl.setContentsMargins(16,0,16,0)
        lf = QLabel("CsixWood  ·  Bálint Bence  ·  Szeged, Selmeci utca 17.")
        lf.setStyleSheet(f"color:{C['text3']};font-size:10px;background:transparent;")
        fl.addWidget(lf); fl.addStretch()
        root.addWidget(footer)

        # Gombok bekötése
        self.btn_back1.clicked.connect(lambda: None)           # nem kell
        self.btn_back2.clicked.connect(lambda: self.goto(0))
        self.btn_back3.clicked.connect(lambda: self.goto(1))
        self.btn_fwd1.clicked.connect(lambda: self.goto(1))
        self.btn_fwd2.clicked.connect(self._p2_next)
        self.btn_fwd3.clicked.connect(self._p3_gen)

        # Step1 fájl betöltő gomb engedélyezi a Továbbot
        self.btn_fwd1.setEnabled(False)
        self.p1.btn_load_ready.connect(lambda: self.btn_fwd1.setEnabled(True))

        self._show_nav(0)

    def _show_nav(self, idx):
        """Csak a megfelelő gombok látszanak."""
        self.btn_back1.setVisible(False)
        self.btn_back2.setVisible(idx == 1)
        self.btn_back3.setVisible(idx == 2)
        self.btn_fwd1.setVisible(idx == 0)
        self.btn_fwd2.setVisible(idx == 1)
        self.btn_fwd3.setVisible(idx == 2)

    def _p2_next(self):
        if not self.munkalepesek:
            QMessageBox.warning(self, "Hiányzó", "Nem választottál munkafolyamatot!")
            return
        self.goto(2)

    def _p3_gen(self):
        self.p3._gen()

    def goto(self, idx):
        self.stack.setCurrentIndex(idx)
        self.stepbar.set_step(idx)
        self._show_nav(idx)

# ══════════════════════════════════════════════════════════════
#  BELÉPŐ PONT
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor(C["bg"]))
    pal.setColor(QPalette.WindowText,      QColor(C["text"]))
    pal.setColor(QPalette.Base,            QColor(C["surface"]))
    pal.setColor(QPalette.AlternateBase,   QColor(C["surface2"]))
    pal.setColor(QPalette.Text,            QColor(C["text"]))
    pal.setColor(QPalette.BrightText,      QColor(C["text"]))
    pal.setColor(QPalette.Button,          QColor(C["surface"]))
    pal.setColor(QPalette.ButtonText,      QColor(C["text"]))
    pal.setColor(QPalette.Highlight,       QColor(C["gold_bg"]))
    pal.setColor(QPalette.HighlightedText, QColor(C["text"]))
    pal.setColor(QPalette.ToolTipBase,     QColor(C["surface"]))
    pal.setColor(QPalette.ToolTipText,     QColor(C["text"]))
    app.setPalette(pal)
    app.setStyleSheet(QSS)

    w = WizardWindow()
    w.show()
    app.exec()
