"""
Kassensystem – Statistik-Dashboard (passwortgeschützt)
Tages-, Wochen-, Monatsauswertung + Top-Produkte
Balkendiagramm direkt auf tkinter Canvas gezeichnet
"""

import tkinter as tk
from tkinter import ttk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config import (
    FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_TITLE, FONT_SIZE_SMALL,
    COLOR_BG, COLOR_SURFACE, COLOR_ACCENT, COLOR_GREEN, COLOR_RED,
    COLOR_TEXT, COLOR_SUBTEXT, COLOR_BORDER, STATISTIK_PASSWORT, BUTTON_HEIGHT
)
from src.ui.passwort_dialog import passwort_pruefen
from src.models.statistik import (
    tagesumsaetze, wochen_umsatz, monats_umsatz,
    top_produkte, zusammenfassung_heute,
    zusammenfassung_woche, zusammenfassung_monat,
)


class StatistikView(tk.Frame):
    """
    Statistik-Tab: Kennzahlen + Diagramm + Top-Produkte.
    Beim ersten Öffnen wird ein Passwort abgefragt.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self._freigeschaltet = False
        self._aktueller_modus = "tag"   # tag | woche | monat
        self._build_lock_screen()

    # ──────────────────────────────────── Sperr-Bildschirm ──────────────────

    def _build_lock_screen(self):
        self._lock_frame = tk.Frame(self, bg=COLOR_BG)
        self._lock_frame.place(relx=0.5, rely=0.45, anchor="center")

        tk.Label(
            self._lock_frame, text="🔒",
            font=(FONT_FAMILY, 56),
            bg=COLOR_BG, fg=COLOR_ACCENT
        ).pack()

        tk.Label(
            self._lock_frame,
            text="Statistik-Dashboard",
            font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT
        ).pack(pady=(8, 4))

        tk.Label(
            self._lock_frame,
            text="Dieses Bereich ist passwortgeschützt.",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=COLOR_BG, fg=COLOR_SUBTEXT
        ).pack(pady=(0, 16))

        tk.Button(
            self._lock_frame,
            text="🔓  Entsperren",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_ACCENT, fg=COLOR_BG,
            activebackground=COLOR_GREEN, activeforeground=COLOR_BG,
            relief="flat", cursor="hand2",
            height=BUTTON_HEIGHT, padx=24,
            command=self._entsperren
        ).pack()

    def _entsperren(self):
        if not passwort_pruefen(self, STATISTIK_PASSWORT):
            return
        self._freigeschaltet = True
        self._lock_frame.place_forget()
        self._build_dashboard()
        self._laden()

    # ──────────────────────────────────────────────── Dashboard ─────────────

    def _build_dashboard(self):
        # ── Header ──────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=COLOR_BG)
        header.pack(fill="x", padx=20, pady=(16, 8))

        tk.Label(
            header, text="Statistiken",
            font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
            bg=COLOR_BG, fg=COLOR_ACCENT
        ).pack(side="left")

        tk.Button(
            header, text="↻  Aktualisieren",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_SURFACE, fg=COLOR_SUBTEXT,
            activebackground=COLOR_ACCENT, activeforeground=COLOR_BG,
            relief="flat", cursor="hand2", padx=10, pady=4,
            command=self._laden
        ).pack(side="right")

        tk.Frame(self, height=1, bg=COLOR_BORDER).pack(fill="x", padx=20)

        # ── KPI-Kacheln ──────────────────────────────────────────────────────
        kpi_row = tk.Frame(self, bg=COLOR_BG)
        kpi_row.pack(fill="x", padx=20, pady=(14, 0))

        self._kpi_heute = self._kpi_kachel(kpi_row, "Heute", "0,00 €", COLOR_ACCENT)
        self._kpi_woche = self._kpi_kachel(kpi_row, "Diese Woche", "0,00 €", COLOR_GREEN)
        self._kpi_monat = self._kpi_kachel(kpi_row, "Dieser Monat", "0,00 €", "#89DCEB")

        # ── Zeitraum-Wahl + Diagramm ─────────────────────────────────────────
        ctrl = tk.Frame(self, bg=COLOR_BG)
        ctrl.pack(fill="x", padx=20, pady=(16, 6))

        tk.Label(
            ctrl, text="Umsatzverlauf",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT
        ).pack(side="left")

        self._modus_buttons = {}
        for key, label in [("tag", "Täglich"), ("woche", "Wöchentlich"), ("monat", "Monatlich")]:
            btn = tk.Button(
                ctrl, text=label,
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                relief="flat", cursor="hand2", padx=10, pady=4,
                command=lambda k=key: self._modus_wechseln(k)
            )
            btn.pack(side="right", padx=(4, 0))
            self._modus_buttons[key] = btn

        # Canvas für Balkendiagramm
        self._chart_canvas = tk.Canvas(
            self, bg=COLOR_SURFACE, highlightthickness=0, height=200
        )
        self._chart_canvas.pack(fill="x", padx=20, pady=(0, 12))

        # ── Zweispaltig unten: Leer-Platz | Top-Produkte ────────────────────
        bottom = tk.Frame(self, bg=COLOR_BG)
        bottom.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        # Top-Produkte rechts
        top_frame = tk.Frame(bottom, bg=COLOR_BG)
        top_frame.pack(side="right", fill="y", padx=(12, 0))

        tk.Label(
            top_frame, text="Top-Produkte",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT
        ).pack(anchor="w", pady=(0, 6))

        self._top_frame_inner = tk.Frame(top_frame, bg=COLOR_SURFACE)
        self._top_frame_inner.pack(fill="both", expand=True)

    def _kpi_kachel(self, parent, titel, wert, farbe) -> tk.Label:
        card = tk.Frame(parent, bg=COLOR_SURFACE)
        card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(
            card, text=titel,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_SURFACE, fg=COLOR_SUBTEXT
        ).pack(anchor="w", padx=14, pady=(12, 2))
        lbl = tk.Label(
            card, text=wert,
            font=(FONT_FAMILY, FONT_SIZE_TITLE + 2, "bold"),
            bg=COLOR_SURFACE, fg=farbe
        )
        lbl.pack(anchor="w", padx=14, pady=(0, 12))
        return lbl

    # ──────────────────────────────────── Laden & Aktualisieren ─────────────

    def _laden(self):
        if not self._freigeschaltet:
            return
        # KPIs
        heute = zusammenfassung_heute()
        woche = zusammenfassung_woche()
        monat = zusammenfassung_monat()
        self._kpi_heute.config(
            text=f"{heute['umsatz_heute']:.2f} €".replace(".", ",")
        )
        self._kpi_woche.config(
            text=f"{woche['umsatz_woche']:.2f} €".replace(".", ",")
        )
        self._kpi_monat.config(
            text=f"{monat['umsatz_monat']:.2f} €".replace(".", ",")
        )
        # Diagramm + Top-Produkte
        self._modus_wechseln(self._aktueller_modus)
        self._top_produkte_laden()

    def _modus_wechseln(self, key: str):
        self._aktueller_modus = key
        # Button-Styling
        for k, btn in self._modus_buttons.items():
            btn.config(
                bg=COLOR_ACCENT if k == key else COLOR_SURFACE,
                fg=COLOR_BG if k == key else COLOR_TEXT
            )
        # Daten laden
        if key == "tag":
            daten = tagesumsaetze(30)
            labels = [d["datum"][-5:] for d in daten]   # MM-DD
        elif key == "woche":
            daten = wochen_umsatz()
            labels = [d["woche"][-3:] for d in daten]   # KWxx
        else:
            daten = monats_umsatz()
            labels = [d["monat"][-2:] for d in daten]   # MM

        werte = [d["umsatz"] for d in daten]
        self._diagramm_zeichnen(werte, labels)

    def _diagramm_zeichnen(self, werte: list, labels: list):
        c = self._chart_canvas
        c.delete("all")
        self.update_idletasks()
        W = c.winfo_width() or 700
        H = c.winfo_height() or 200

        pad_l, pad_r, pad_t, pad_b = 48, 10, 16, 30
        chart_w = W - pad_l - pad_r
        chart_h = H - pad_t - pad_b

        if not werte:
            c.create_text(
                W // 2, H // 2,
                text="Noch keine Daten für diesen Zeitraum.",
                fill=COLOR_SUBTEXT,
                font=(FONT_FAMILY, FONT_SIZE_SMALL)
            )
            return

        max_val = max(werte) if werte else 1
        if max_val == 0:
            max_val = 1

        n = len(werte)
        bar_w = max(4, chart_w // n - 4)

        # Y-Achse Beschriftung (4 Stufen)
        for i in range(5):
            y_val = max_val * i / 4
            y_px = pad_t + chart_h - (chart_h * i / 4)
            c.create_line(pad_l - 4, y_px, pad_l, y_px, fill=COLOR_BORDER, width=1)
            c.create_line(pad_l, y_px, W - pad_r, y_px,
                          fill=COLOR_BORDER, width=1, dash=(2, 6))
            c.create_text(
                pad_l - 6, y_px,
                text=f"{y_val:.0f}",
                anchor="e", fill=COLOR_SUBTEXT,
                font=(FONT_FAMILY, 8)
            )

        # Balken zeichnen
        for i, (val, lbl) in enumerate(zip(werte, labels)):
            x0 = pad_l + i * (chart_w / n) + (chart_w / n - bar_w) / 2
            x1 = x0 + bar_w
            bar_h = (val / max_val) * chart_h
            y0 = pad_t + chart_h - bar_h
            y1 = pad_t + chart_h

            # Balken mit abgerundeten Ecken (simuliert durch Rechteck)
            c.create_rectangle(x0, y0, x1, y1, fill=COLOR_ACCENT,
                                outline="", width=0)

            # Wert oben (nur wenn genug Platz)
            if bar_h > 18:
                c.create_text(
                    (x0 + x1) / 2, y0 + 8,
                    text=f"{val:.0f}",
                    fill=COLOR_BG,
                    font=(FONT_FAMILY, 8, "bold")
                )

            # X-Label unten (jedes 2. bei mehr als 20 Einträgen)
            if n <= 14 or i % 2 == 0:
                c.create_text(
                    (x0 + x1) / 2, H - pad_b + 8,
                    text=lbl,
                    fill=COLOR_SUBTEXT,
                    font=(FONT_FAMILY, 8)
                )

    def _top_produkte_laden(self):
        for w in self._top_frame_inner.winfo_children():
            w.destroy()

        produkte = top_produkte(10)
        if not produkte:
            tk.Label(
                self._top_frame_inner,
                text="Noch keine Daten.",
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                bg=COLOR_SURFACE, fg=COLOR_SUBTEXT
            ).pack(padx=12, pady=8)
            return

        # Kopfzeile
        head = tk.Frame(self._top_frame_inner, bg=COLOR_SURFACE)
        head.pack(fill="x")
        for text, anchor, w in [("Produkt", "w", 0), ("Menge", "e", 7), ("Umsatz", "e", 10)]:
            tk.Label(
                head, text=text,
                font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
                bg=COLOR_SURFACE, fg=COLOR_SUBTEXT,
                anchor=anchor, width=w if w else None
            ).pack(side="left" if anchor == "w" else "right", padx=(8, 8), pady=6)

        tk.Frame(self._top_frame_inner, height=1, bg=COLOR_BORDER).pack(
            fill="x", padx=4
        )

        for i, prod in enumerate(produkte):
            row_bg = COLOR_BG if i % 2 == 0 else COLOR_SURFACE
            row = tk.Frame(self._top_frame_inner, bg=row_bg)
            row.pack(fill="x")

            tk.Label(
                row, text=f"{i+1}. {prod['name']}",
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                bg=row_bg, fg=COLOR_TEXT, anchor="w"
            ).pack(side="left", padx=8, pady=4, fill="x", expand=True)

            tk.Label(
                row, text=f"{prod['menge']}×",
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                bg=row_bg, fg=COLOR_ACCENT, anchor="e", width=6
            ).pack(side="right", padx=(0, 4))

            tk.Label(
                row, text=f"{prod['umsatz']:.2f} €",
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                bg=row_bg, fg=COLOR_TEXT, anchor="e", width=10
            ).pack(side="right", padx=4)

    def refresh(self):
        if self._freigeschaltet:
            self._laden()
