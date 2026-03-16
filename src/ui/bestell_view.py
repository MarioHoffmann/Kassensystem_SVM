"""
Kassensystem – Bestellansicht (linke Sidebar, unterhalb Personenauswahl)
Zeigt aktuelle Bestellpositionen + Gesamtpreis + „Bestellung fertig"-Button
"""

import tkinter as tk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config import (
    FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_TITLE, FONT_SIZE_SMALL,
    COLOR_BG, COLOR_SIDEBAR, COLOR_SURFACE, COLOR_ACCENT,
    COLOR_GREEN, COLOR_RED, COLOR_TEXT, COLOR_SUBTEXT, COLOR_BORDER,
    BUTTON_HEIGHT
)
from src.models.bestellung import (
    get_oder_erstelle_bestellung, positionen_der_bestellung,
    produkt_hinzufuegen, position_entfernen, menge_aendern,
    gesamtpreis_berechnen, bestellung_abschliessen
)


class BestellView(tk.Frame):
    """
    Bestellübersicht-Widget für die linke Sidebar.
    Wird angezeigt, sobald eine Person ausgewählt ist.

    Aufbau:
    ┌─────────────────────────────┐
    │  Bestellung für: [Name]     │
    │─────────────────────────────│
    │  [−] 2×  Cola     5.00 €  [×] │
    │  [−] 1×  Pizza    8.00 €  [×] │
    │─────────────────────────────│
    │  Gesamt:          13.00 €   │
    │  [ Bestellung fertig ]      │
    └─────────────────────────────┘
    """

    def __init__(self, parent, on_abgeschlossen=None, **kwargs):
        super().__init__(parent, bg=COLOR_SIDEBAR, **kwargs)
        self._on_abgeschlossen = on_abgeschlossen
        self._person = None
        self._bestellung_id = None
        self._build_ui()

    # ──────────────────────────────────────────────── UI-Aufbau ─────────────

    def _build_ui(self):
        # Trennlinie oben
        tk.Frame(self, height=1, bg=COLOR_BORDER).pack(fill="x")

        # Titel
        self._titel_var = tk.StringVar(value="Bestellung")
        tk.Label(
            self,
            textvariable=self._titel_var,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_SIDEBAR, fg=COLOR_TEXT,
        ).pack(pady=(12, 4), padx=16, anchor="w")

        # Scrollbarer Bereich für Positionen
        container = tk.Frame(self, bg=COLOR_SIDEBAR)
        container.pack(fill="both", expand=True, padx=8)

        self._canvas = tk.Canvas(
            container, bg=COLOR_SIDEBAR, highlightthickness=0
        )
        scrollbar = tk.Scrollbar(
            container, orient="vertical", command=self._canvas.yview
        )
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._pos_frame = tk.Frame(self._canvas, bg=COLOR_SIDEBAR)
        self._canvas_win = self._canvas.create_window(
            (0, 0), window=self._pos_frame, anchor="nw"
        )
        self._pos_frame.bind(
            "<Configure>",
            lambda e: self._canvas.config(scrollregion=self._canvas.bbox("all"))
        )
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfig(self._canvas_win, width=e.width)
        )

        # Fußzeile: Gesamtpreis + Button
        footer = tk.Frame(self, bg=COLOR_SIDEBAR)
        footer.pack(fill="x", padx=12, pady=8)

        tk.Frame(footer, height=1, bg=COLOR_BORDER).pack(fill="x", pady=(0, 8))

        gesamt_row = tk.Frame(footer, bg=COLOR_SIDEBAR)
        gesamt_row.pack(fill="x")

        tk.Label(
            gesamt_row, text="Gesamt:",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_SIDEBAR, fg=COLOR_TEXT
        ).pack(side="left")

        self._gesamt_var = tk.StringVar(value="0,00 €")
        tk.Label(
            gesamt_row,
            textvariable=self._gesamt_var,
            font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
            bg=COLOR_SIDEBAR, fg=COLOR_ACCENT
        ).pack(side="right")

        self._btn_fertig = tk.Button(
            footer,
            text="✓  Bestellung fertig",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_GREEN, fg=COLOR_SIDEBAR,
            activebackground=COLOR_ACCENT, activeforeground=COLOR_SIDEBAR,
            relief="flat", cursor="hand2",
            height=BUTTON_HEIGHT,
            command=self._bestellung_abschliessen,
        )
        self._btn_fertig.pack(fill="x", pady=(8, 4), ipady=4)

    # ────────────────────────────────────────────── Öffentliche API ──────────

    def set_person(self, person: dict | None):
        """Person setzen → Bestellung laden oder zurücksetzen."""
        self._person = person
        if person:
            self._bestellung_id = get_oder_erstelle_bestellung(person["id"])
            self._titel_var.set(
                f"Bestellung: {person['nachname']}, {person['vorname']}"
            )
        else:
            self._bestellung_id = None
            self._titel_var.set("Bestellung")
        self._refresh()

    def produkt_hinzufuegen(self, produkt: dict):
        """Produkt zur aktiven Bestellung hinzufügen."""
        if not self._bestellung_id:
            return
        produkt_hinzufuegen(
            self._bestellung_id, produkt["id"], produkt["preis"]
        )
        self._refresh()

    def refresh(self):
        self._refresh()

    # ────────────────────────────────────────────── Intern ──────────────────

    def _refresh(self):
        """Positionen und Gesamtpreis neu aufbauen."""
        for w in self._pos_frame.winfo_children():
            w.destroy()

        if not self._bestellung_id:
            tk.Label(
                self._pos_frame,
                text="Keine Person ausgewählt.",
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                bg=COLOR_SIDEBAR, fg=COLOR_SUBTEXT,
            ).pack(pady=8, padx=8, anchor="w")
            self._gesamt_var.set("0,00 €")
            return

        positionen = positionen_der_bestellung(self._bestellung_id)

        if not positionen:
            tk.Label(
                self._pos_frame,
                text="Noch keine Produkte.\nProdukt rechts anklicken.",
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                bg=COLOR_SIDEBAR, fg=COLOR_SUBTEXT,
                justify="left",
            ).pack(pady=8, padx=8, anchor="w")
        else:
            for pos in positionen:
                self._position_zeile(pos)

        gesamt = gesamtpreis_berechnen(self._bestellung_id)
        self._gesamt_var.set(f"{gesamt:.2f} €".replace(".", ","))

    def _position_zeile(self, pos: dict):
        """Einzelne Zeile für eine Bestellposition."""
        row = tk.Frame(self._pos_frame, bg=COLOR_SURFACE)
        row.pack(fill="x", pady=2, padx=2)

        # Mengen-Steuerung [−] Menge [+]
        btn_minus = tk.Button(
            row, text="−",
            font=(FONT_FAMILY, 11, "bold"),
            bg=COLOR_SURFACE, fg=COLOR_RED,
            activebackground=COLOR_SURFACE,
            relief="flat", cursor="hand2", width=2,
            command=lambda pid=pos["id"]: self._menge_aendern(pid, -1)
        )
        btn_minus.pack(side="left", padx=(6, 2), pady=6)

        tk.Label(
            row,
            text=f"{pos['menge']}×",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
            bg=COLOR_SURFACE, fg=COLOR_ACCENT, width=3, anchor="e"
        ).pack(side="left")

        # Produktname (nimmt den verfügbaren Platz)
        tk.Label(
            row,
            text=pos["produkt_name"],
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_SURFACE, fg=COLOR_TEXT,
            anchor="w",
        ).pack(side="left", padx=6, fill="x", expand=True)

        # Einzelpreis × Menge
        tk.Label(
            row,
            text=f"{pos['gesamtpreis']:.2f} €",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
            bg=COLOR_SURFACE, fg=COLOR_TEXT,
            anchor="e", width=8,
        ).pack(side="right", padx=4)

        # Löschen-Button [×]
        tk.Button(
            row, text="✕",
            font=(FONT_FAMILY, 10),
            bg=COLOR_SURFACE, fg=COLOR_SUBTEXT,
            activebackground=COLOR_SURFACE,
            relief="flat", cursor="hand2",
            command=lambda pid=pos["id"]: self._position_entfernen(pid)
        ).pack(side="right", padx=4)

    def _menge_aendern(self, position_id: int, delta: int):
        menge_aendern(position_id, delta)
        self._refresh()

    def _position_entfernen(self, position_id: int):
        position_entfernen(position_id)
        self._refresh()

    def _bestellung_abschliessen(self):
        if not self._bestellung_id:
            return
        positionen = positionen_der_bestellung(self._bestellung_id)
        if not positionen:
            return

        gesamt = gesamtpreis_berechnen(self._bestellung_id)
        bestellung_abschliessen(self._bestellung_id)

        # Neue Bestellung für gleiche Person vorbereiten
        self._bestellung_id = get_oder_erstelle_bestellung(self._person["id"])
        self._refresh()

        if self._on_abgeschlossen:
            self._on_abgeschlossen(gesamt)
