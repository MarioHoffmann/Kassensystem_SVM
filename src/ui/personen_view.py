"""
Kassensystem – Personenverwaltungs-UI
Linke Spalte: Formular + alphabetisches Dropdown
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config import (
    FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_TITLE, FONT_SIZE_SMALL,
    COLOR_BG, COLOR_SIDEBAR, COLOR_SURFACE, COLOR_ACCENT,
    COLOR_GREEN, COLOR_RED, COLOR_TEXT, COLOR_SUBTEXT, COLOR_BORDER,
    BUTTON_HEIGHT, DROPDOWN_WIDTH
)
from src.models.person import alle_personen, person_anlegen, PersonError


class PersonenView(tk.Frame):
    """
    Linke Seitenleiste mit:
    - Formular zum Anlegen einer Person (Vorname + Nachname)
    - Alphabetisches Dropdown zur Personenauswahl
    - Callback bei Auswahl einer Person
    """

    def __init__(self, parent, on_person_selected=None, **kwargs):
        super().__init__(parent, bg=COLOR_SIDEBAR, **kwargs)
        self._on_person_selected = on_person_selected
        self._ausgewaehlte_person = None

        self._build_ui()
        self._personen_laden()

    # ------------------------------------------------------------------ UI --

    def _build_ui(self):
        # ── Titel ──────────────────────────────────────────────────────────
        tk.Label(
            self,
            text="Personenverwaltung",
            font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
            bg=COLOR_SIDEBAR,
            fg=COLOR_ACCENT,
        ).pack(pady=(20, 4), padx=16, anchor="w")

        tk.Frame(self, height=1, bg=COLOR_BORDER).pack(fill="x", padx=16, pady=(0, 14))

        # ── Formular ───────────────────────────────────────────────────────
        form = tk.Frame(self, bg=COLOR_SIDEBAR)
        form.pack(fill="x", padx=16)

        # Vorname
        tk.Label(form, text="Vorname *", font=(FONT_FAMILY, FONT_SIZE_SMALL),
                 bg=COLOR_SIDEBAR, fg=COLOR_SUBTEXT).grid(row=0, column=0, sticky="w", pady=(0, 2))
        self._vorname_var = tk.StringVar()
        self._entry_vorname = self._make_entry(form, self._vorname_var)
        self._entry_vorname.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self._entry_vorname.bind("<Return>", lambda e: self._entry_nachname.focus_set())

        # Nachname
        tk.Label(form, text="Nachname *", font=(FONT_FAMILY, FONT_SIZE_SMALL),
                 bg=COLOR_SIDEBAR, fg=COLOR_SUBTEXT).grid(row=2, column=0, sticky="w", pady=(0, 2))
        self._nachname_var = tk.StringVar()
        self._entry_nachname = self._make_entry(form, self._nachname_var)
        self._entry_nachname.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        self._entry_nachname.bind("<Return>", lambda e: self._person_anlegen())

        form.columnconfigure(0, weight=1)

        # Button „Person anlegen"
        self._btn_anlegen = tk.Button(
            form,
            text="＋  Person anlegen",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_ACCENT,
            fg=COLOR_BG,
            activebackground=COLOR_GREEN,
            activeforeground=COLOR_BG,
            relief="flat",
            cursor="hand2",
            height=BUTTON_HEIGHT,
            command=self._person_anlegen,
        )
        self._btn_anlegen.grid(row=4, column=0, sticky="ew", ipady=4)

        # Statusmeldung
        self._status_var = tk.StringVar()
        self._status_label = tk.Label(
            form,
            textvariable=self._status_var,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_SIDEBAR,
            fg=COLOR_GREEN,
            wraplength=220,
            justify="left",
        )
        self._status_label.grid(row=5, column=0, sticky="w", pady=(6, 0))

        # ── Trennlinie ─────────────────────────────────────────────────────
        tk.Frame(self, height=1, bg=COLOR_BORDER).pack(fill="x", padx=16, pady=18)

        # ── Dropdown zur Personenauswahl ────────────────────────────────────
        tk.Label(
            self,
            text="Person auswählen",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_SIDEBAR,
            fg=COLOR_TEXT,
        ).pack(padx=16, anchor="w", pady=(0, 6))

        dropdown_frame = tk.Frame(self, bg=COLOR_SIDEBAR)
        dropdown_frame.pack(fill="x", padx=16)

        self._auswahl_var = tk.StringVar(value="— bitte wählen —")
        self._dropdown = tk.OptionMenu(
            dropdown_frame,
            self._auswahl_var,
            "— bitte wählen —",
            command=self._person_ausgewaehlt,
        )
        self._dropdown.config(
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_BG,
            relief="flat",
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            width=DROPDOWN_WIDTH,
            anchor="w",
        )
        self._dropdown["menu"].config(
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT,
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_BG,
        )
        self._dropdown.pack(fill="x")

        # Aktive Personenanzeige (nach Auswahl)
        self._aktiv_frame = tk.Frame(self, bg=COLOR_SURFACE, bd=0)
        self._aktiv_label = tk.Label(
            self._aktiv_frame,
            text="",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_SURFACE,
            fg=COLOR_ACCENT,
            anchor="w",
        )
        self._aktiv_label.pack(side="left", padx=12, pady=10, fill="x", expand=True)

        # Button zum Abwählen
        tk.Button(
            self._aktiv_frame,
            text="✕",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=COLOR_SURFACE,
            fg=COLOR_RED,
            activebackground=COLOR_SURFACE,
            relief="flat",
            cursor="hand2",
            command=self._person_abwaehlen,
        ).pack(side="right", padx=8)

    # ─────────────────────────────────────────────── Hilfsmethoden ──────────

    def _make_entry(self, parent, textvariable) -> tk.Entry:
        e = tk.Entry(
            parent,
            textvariable=textvariable,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT,
            insertbackground=COLOR_TEXT,
            relief="flat",
            bd=8,
        )
        return e

    def _set_status(self, msg: str, error: bool = False):
        self._status_var.set(msg)
        self._status_label.config(fg=COLOR_RED if error else COLOR_GREEN)

    # ─────────────────────────────────────────────── Logik ──────────────────

    def _personen_laden(self):
        """Lädt alle Personen aus der DB und aktualisiert das Dropdown."""
        personen = alle_personen()
        menu = self._dropdown["menu"]
        menu.delete(0, "end")
        menu.add_command(
            label="— bitte wählen —",
            command=lambda: self._auswahl_var.set("— bitte wählen —"),
        )
        for p in personen:
            label = f"{p['nachname']}, {p['vorname']}"
            menu.add_command(
                label=label,
                command=lambda l=label, pid=p['id'], pn=p: self._person_ausgewaehlt(l, pn),
            )
        if not personen:
            self._auswahl_var.set("— noch keine Personen —")

    def _person_anlegen(self):
        vorname = self._vorname_var.get()
        nachname = self._nachname_var.get()
        try:
            person_anlegen(vorname, nachname)
            self._vorname_var.set("")
            self._nachname_var.set("")
            self._entry_vorname.focus_set()
            self._set_status(f"✓ {vorname} {nachname} angelegt.")
            self._personen_laden()
        except PersonError as e:
            self._set_status(str(e), error=True)

    def _person_ausgewaehlt(self, label, person=None):
        if label.startswith("—"):
            return
        self._ausgewaehlte_person = person
        self._auswahl_var.set(label)
        # Aktive Anzeige einblenden
        self._aktiv_label.config(text=f"👤  {label}")
        self._aktiv_frame.pack(fill="x", padx=16, pady=(10, 0))
        # Callback
        if self._on_person_selected and person:
            self._on_person_selected(person)

    def _person_abwaehlen(self):
        self._ausgewaehlte_person = None
        self._auswahl_var.set("— bitte wählen —")
        self._aktiv_frame.pack_forget()
        if self._on_person_selected:
            self._on_person_selected(None)

    def get_ausgewaehlte_person(self):
        return self._ausgewaehlte_person

    def refresh(self):
        self._personen_laden()
