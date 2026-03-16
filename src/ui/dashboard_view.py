"""
Kassensystem – Dashboard: Offene Beträge
Übersicht aller Gäste mit unbezahlten Bestellungen + Detailansicht + Bezahlen
"""

import tkinter as tk
from tkinter import ttk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config import (
    FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_TITLE, FONT_SIZE_SMALL,
    COLOR_BG, COLOR_SURFACE, COLOR_ACCENT, COLOR_GREEN, COLOR_RED,
    COLOR_TEXT, COLOR_SUBTEXT, COLOR_BORDER, BUTTON_HEIGHT
)
from src.models.dashboard import (
    gaeste_mit_offenen_betraegen,
    offene_bestellungen_der_person,
    person_als_bezahlt_markieren,
    gesamt_offen_fuer_person,
)


class DashboardView(tk.Frame):
    """
    Dashboard-Tab: Offene Beträge

    Layout:
    ┌─────────────────────────────────────────────────┐
    │  Offene Beträge                [Aktualisieren]  │
    ├────────────────────────┬────────────────────────┤
    │  Gästeliste (links)    │  Detailansicht (rechts) │
    │  Dropdown + Karten     │  Bestellpositionen      │
    │                        │  Gesamtbetrag           │
    │                        │  [Bezahlt]              │
    └────────────────────────┴────────────────────────┘
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self._aktive_person = None
        self._build_ui()
        self._laden()

    # ──────────────────────────────────────────────── Aufbau ────────────────

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=COLOR_BG)
        header.pack(fill="x", padx=20, pady=(16, 8))

        tk.Label(
            header, text="Offene Beträge",
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

        # ── Zweispaltig ──────────────────────────────────────────────────────
        body = tk.Frame(self, bg=COLOR_BG)
        body.pack(fill="both", expand=True, padx=20, pady=12)

        # Linke Spalte: Gästeliste + Dropdown-Suche
        left = tk.Frame(body, bg=COLOR_BG, width=320)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self._build_left(left)

        tk.Frame(body, width=1, bg=COLOR_BORDER).pack(side="left", fill="y", padx=12)

        # Rechte Spalte: Detailansicht
        right = tk.Frame(body, bg=COLOR_BG)
        right.pack(side="left", fill="both", expand=True)
        self._build_right(right)

    def _build_left(self, parent):
        # Alphabetisches Dropdown / Suche
        tk.Label(
            parent, text="Person auswählen",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_BG, fg=COLOR_SUBTEXT
        ).pack(anchor="w", pady=(0, 4))

        self._dropdown_var = tk.StringVar(value="— alle anzeigen —")
        self._dropdown = tk.OptionMenu(
            parent, self._dropdown_var, "— alle anzeigen —",
            command=self._dropdown_gewaehlt
        )
        self._dropdown.config(
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=COLOR_SURFACE, fg=COLOR_TEXT,
            activebackground=COLOR_ACCENT, activeforeground=COLOR_BG,
            relief="flat", bd=0, highlightthickness=0,
            cursor="hand2", anchor="w", width=26
        )
        self._dropdown["menu"].config(
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_SURFACE, fg=COLOR_TEXT,
            activebackground=COLOR_ACCENT, activeforeground=COLOR_BG,
        )
        self._dropdown.pack(fill="x", pady=(0, 12))

        # Scrollbare Gästekarten
        canvas = tk.Canvas(parent, bg=COLOR_BG, highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._gaeste_frame = tk.Frame(canvas, bg=COLOR_BG)
        win = canvas.create_window((0, 0), window=self._gaeste_frame, anchor="nw")
        self._gaeste_frame.bind(
            "<Configure>",
            lambda e: canvas.config(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(win, width=e.width)
        )

    def _build_right(self, parent):
        # Leer wenn keine Person gewählt
        self._detail_placeholder = tk.Frame(parent, bg=COLOR_BG)
        self._detail_placeholder.place(relx=0.5, rely=0.4, anchor="center")

        tk.Label(
            self._detail_placeholder, text="👤",
            font=(FONT_FAMILY, 48),
            bg=COLOR_BG, fg=COLOR_ACCENT
        ).pack()
        tk.Label(
            self._detail_placeholder,
            text="Person links auswählen\num Details zu sehen.",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=COLOR_BG, fg=COLOR_SUBTEXT, justify="center"
        ).pack(pady=8)

        # Detailansicht (initial versteckt)
        self._detail_frame = tk.Frame(parent, bg=COLOR_BG)

        # Personenname
        self._detail_name_var = tk.StringVar()
        tk.Label(
            self._detail_frame,
            textvariable=self._detail_name_var,
            font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT
        ).pack(anchor="w", pady=(0, 8))

        tk.Frame(self._detail_frame, height=1, bg=COLOR_BORDER).pack(
            fill="x", pady=(0, 10)
        )

        # Scrollbarer Bereich für Bestelldetails
        detail_canvas = tk.Canvas(
            self._detail_frame, bg=COLOR_BG, highlightthickness=0
        )
        detail_sb = ttk.Scrollbar(
            self._detail_frame, orient="vertical", command=detail_canvas.yview
        )
        detail_canvas.configure(yscrollcommand=detail_sb.set)
        detail_sb.pack(side="right", fill="y")
        detail_canvas.pack(side="left", fill="both", expand=True)

        self._bestellungen_frame = tk.Frame(detail_canvas, bg=COLOR_BG)
        detail_win = detail_canvas.create_window(
            (0, 0), window=self._bestellungen_frame, anchor="nw"
        )
        self._bestellungen_frame.bind(
            "<Configure>",
            lambda e: detail_canvas.config(
                scrollregion=detail_canvas.bbox("all")
            )
        )
        detail_canvas.bind(
            "<Configure>",
            lambda e: detail_canvas.itemconfig(detail_win, width=e.width)
        )

        # Fußzeile der Detailansicht
        self._detail_footer = tk.Frame(parent, bg=COLOR_BG)

        gesamt_row = tk.Frame(self._detail_footer, bg=COLOR_BG)
        gesamt_row.pack(fill="x", pady=(8, 6))

        tk.Label(
            gesamt_row, text="Offener Betrag:",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT
        ).pack(side="left")

        self._gesamt_detail_var = tk.StringVar()
        tk.Label(
            gesamt_row,
            textvariable=self._gesamt_detail_var,
            font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
            bg=COLOR_BG, fg=COLOR_RED
        ).pack(side="right")

        tk.Button(
            self._detail_footer,
            text="💳  Bezahlt",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL + 2, "bold"),
            bg=COLOR_GREEN, fg=COLOR_BG,
            activebackground=COLOR_ACCENT, activeforeground=COLOR_BG,
            relief="flat", cursor="hand2",
            height=BUTTON_HEIGHT,
            command=self._bezahlen
        ).pack(fill="x", ipady=6)

    # ──────────────────────────────────────────────── Laden ─────────────────

    def _laden(self):
        self._aktive_person = None
        gaeste = gaeste_mit_offenen_betraegen()

        # Dropdown aktualisieren
        menu = self._dropdown["menu"]
        menu.delete(0, "end")
        self._dropdown_personen = {}
        menu.add_command(
            label="— alle anzeigen —",
            command=lambda: (
                self._dropdown_var.set("— alle anzeigen —"),
                self._gaeste_laden(gaeste)
            )
        )
        for g in gaeste:
            label = f"{g['nachname']}, {g['vorname']}"
            self._dropdown_personen[label] = g
            menu.add_command(
                label=label,
                command=lambda l=label, gg=g: self._dropdown_gewaehlt(l, gg)
            )

        self._dropdown_var.set("— alle anzeigen —")
        self._gaeste_laden(gaeste)
        self._detail_zuruecksetzen()

    def _gaeste_laden(self, gaeste: list[dict]):
        for w in self._gaeste_frame.winfo_children():
            w.destroy()

        if not gaeste:
            tk.Label(
                self._gaeste_frame,
                text="✓  Keine offenen Beträge.",
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                bg=COLOR_BG, fg=COLOR_GREEN
            ).pack(pady=20, anchor="w")
            return

        for g in gaeste:
            self._gast_karte(g)

    def _gast_karte(self, gast: dict):
        card = tk.Frame(
            self._gaeste_frame, bg=COLOR_SURFACE, cursor="hand2"
        )
        card.pack(fill="x", pady=4, padx=2)

        # Klick → Detailansicht öffnen
        for w in [card]:
            w.bind("<Button-1>", lambda e, g=gast: self._person_select(g))

        name_lbl = tk.Label(
            card,
            text=f"{gast['nachname']}, {gast['vorname']}",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_SURFACE, fg=COLOR_TEXT,
            anchor="w", cursor="hand2"
        )
        name_lbl.pack(side="left", padx=12, pady=10, fill="x", expand=True)
        name_lbl.bind("<Button-1>", lambda e, g=gast: self._person_select(g))

        betrag_lbl = tk.Label(
            card,
            text=f"{gast['offener_betrag']:.2f} €",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_SURFACE, fg=COLOR_RED,
            anchor="e", cursor="hand2"
        )
        betrag_lbl.pack(side="right", padx=12)
        betrag_lbl.bind("<Button-1>", lambda e, g=gast: self._person_select(g))

    def _dropdown_gewaehlt(self, label, gast=None):
        if label.startswith("—"):
            return
        if gast is None:
            gast = self._dropdown_personen.get(label)
        if gast:
            self._person_select(gast)

    def _person_select(self, gast: dict):
        self._aktive_person = gast
        self._detail_zeigen(gast)

    # ──────────────────────────────────────────────── Detailansicht ─────────

    def _detail_zeigen(self, gast: dict):
        self._detail_placeholder.place_forget()
        self._detail_frame.pack(fill="both", expand=True, padx=4)
        self._detail_footer.pack(fill="x", padx=4, pady=(0, 8))

        self._detail_name_var.set(
            f"{gast['nachname']}, {gast['vorname']}"
        )

        for w in self._bestellungen_frame.winfo_children():
            w.destroy()

        bestellungen = offene_bestellungen_der_person(gast["id"])
        for i, b in enumerate(bestellungen):
            self._bestellung_block(b, i + 1, len(bestellungen))

        gesamt = gesamt_offen_fuer_person(gast["id"])
        self._gesamt_detail_var.set(f"{gesamt:.2f} €")

    def _bestellung_block(self, b: dict, nr: int, total: int):
        block = tk.Frame(self._bestellungen_frame, bg=COLOR_BG)
        block.pack(fill="x", pady=(0, 8))

        header_text = f"Bestellung {nr}"
        if total > 1:
            header_text += f" von {total}"
        header_text += f"  –  {b['erstellt_am'][:16]}"

        tk.Label(
            block, text=header_text,
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
            bg=COLOR_BG, fg=COLOR_SUBTEXT
        ).pack(anchor="w", pady=(0, 4))

        # Positionstabelle
        table = tk.Frame(block, bg=COLOR_SURFACE)
        table.pack(fill="x")

        # Kopfzeile
        headers = [("Menge", 6), ("Produkt", 0), ("Einzel", 9), ("Gesamt", 9)]
        for col, (h, w) in enumerate(headers):
            tk.Label(
                table, text=h,
                font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
                bg=COLOR_SURFACE, fg=COLOR_SUBTEXT,
                width=w if w else None, anchor="w" if col == 1 else "e"
            ).grid(row=0, column=col, padx=8, pady=4, sticky="w" if col == 1 else "e")

        tk.Frame(table, height=1, bg=COLOR_BORDER).grid(
            row=1, column=0, columnspan=4, sticky="ew", padx=4
        )

        for i, pos in enumerate(b["positionen"]):
            row_bg = COLOR_SURFACE
            tk.Label(table, text=f"{pos['menge']}×",
                     font=(FONT_FAMILY, FONT_SIZE_SMALL),
                     bg=row_bg, fg=COLOR_ACCENT, width=6, anchor="e"
                     ).grid(row=i + 2, column=0, padx=8, pady=3, sticky="e")
            tk.Label(table, text=pos["produkt_name"],
                     font=(FONT_FAMILY, FONT_SIZE_SMALL),
                     bg=row_bg, fg=COLOR_TEXT, anchor="w"
                     ).grid(row=i + 2, column=1, padx=8, sticky="ew")
            tk.Label(table, text=f"{pos['einzelpreis']:.2f} €",
                     font=(FONT_FAMILY, FONT_SIZE_SMALL),
                     bg=row_bg, fg=COLOR_TEXT, width=9, anchor="e"
                     ).grid(row=i + 2, column=2, padx=8, sticky="e")
            tk.Label(table, text=f"{pos['gesamtpreis']:.2f} €",
                     font=(FONT_FAMILY, FONT_SIZE_SMALL),
                     bg=row_bg, fg=COLOR_TEXT, width=9, anchor="e"
                     ).grid(row=i + 2, column=3, padx=8, sticky="e")

        table.columnconfigure(1, weight=1)

        # Zwischensumme
        tk.Label(
            block,
            text=f"Zwischensumme: {b['summe']:.2f} €",
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT, anchor="e"
        ).pack(fill="x", pady=(4, 0))

        tk.Frame(block, height=1, bg=COLOR_BORDER).pack(fill="x", pady=6)

    def _detail_zuruecksetzen(self):
        self._detail_frame.pack_forget()
        self._detail_footer.pack_forget()
        self._detail_placeholder.place(relx=0.5, rely=0.4, anchor="center")

    # ──────────────────────────────────────────────── Bezahlen ──────────────

    def _bezahlen(self):
        if not self._aktive_person:
            return
        person_als_bezahlt_markieren(self._aktive_person["id"])
        self._bezahlt_toast(self._aktive_person)
        self._laden()

    def _bezahlt_toast(self, person: dict):
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.configure(bg=COLOR_GREEN)
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - 180
        y = self.winfo_rooty() + 40
        toast.geometry(f"360x60+{x}+{y}")
        tk.Label(
            toast,
            text=f"✓  {person['nachname']}, {person['vorname']} – Bezahlt!",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_GREEN, fg=COLOR_BG, pady=18
        ).pack(fill="both", expand=True)
        toast.after(2500, toast.destroy)
