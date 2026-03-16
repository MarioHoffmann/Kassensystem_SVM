"""
Kassensystem – Produktverwaltungs-UI
Rechte Seite: Kategorien-Tabs + Produktkarten + Bearbeitung mit Passwortschutz
"""

import tkinter as tk
from tkinter import ttk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config import (
    FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_TITLE, FONT_SIZE_SMALL,
    COLOR_BG, COLOR_SIDEBAR, COLOR_SURFACE, COLOR_ACCENT,
    COLOR_GREEN, COLOR_RED, COLOR_TEXT, COLOR_SUBTEXT, COLOR_BORDER,
    BUTTON_HEIGHT
)
from src.models.produkt import (
    alle_kategorien, kategorie_anlegen, kategorie_loeschen,
    produkte_der_kategorie, produkt_anlegen, produkt_bearbeiten,
    produkt_loeschen, KategorieError, ProduktError
)
from src.ui.passwort_dialog import passwort_pruefen


class ProduktView(tk.Frame):
    """
    Produktverwaltung:
    - Oben: Kategorie-Tabs (scrollbar bei vielen)
    - Mitte: Produktkarten der ausgewählten Kategorie
    - Unten: Formular zum Anlegen neuer Kategorien/Produkte
    - Bearbeitung/Löschen nur mit Passwort
    - Callback on_produkt_clicked(produkt_dict) für den Bestellvorgang
    """

    def __init__(self, parent, on_produkt_clicked=None, **kwargs):
        super().__init__(parent, bg=COLOR_BG, **kwargs)
        self._on_produkt_clicked = on_produkt_clicked
        self._aktive_kategorie_id = None
        self._build_ui()
        self._kategorien_laden()

    # ─────────────────────────────────────────────── UI-Aufbau ──────────────

    def _build_ui(self):
        # ── Titelzeile + Verwaltungs-Button ─────────────────────────────────
        header = tk.Frame(self, bg=COLOR_BG)
        header.pack(fill="x", padx=20, pady=(16, 8))

        tk.Label(
            header, text="Produkte",
            font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
            bg=COLOR_BG, fg=COLOR_ACCENT
        ).pack(side="left")

        tk.Button(
            header, text="⚙  Verwalten",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_SURFACE, fg=COLOR_SUBTEXT,
            activebackground=COLOR_ACCENT, activeforeground=COLOR_BG,
            relief="flat", cursor="hand2", padx=10, pady=4,
            command=self._verwaltung_oeffnen
        ).pack(side="right")

        tk.Frame(self, height=1, bg=COLOR_BORDER).pack(fill="x", padx=20)

        # ── Kategorie-Leiste (horizontale Tabs) ─────────────────────────────
        self._tab_frame = tk.Frame(self, bg=COLOR_BG)
        self._tab_frame.pack(fill="x", padx=20, pady=(12, 0))

        # ── Produkt-Gitter (scrollbar) ───────────────────────────────────────
        canvas_frame = tk.Frame(self, bg=COLOR_BG)
        canvas_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self._canvas = tk.Canvas(canvas_frame, bg=COLOR_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical",
                                  command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._produkt_grid = tk.Frame(self._canvas, bg=COLOR_BG)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._produkt_grid, anchor="nw"
        )

        self._produkt_grid.bind("<Configure>", self._on_grid_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_grid_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ─────────────────────────────────────────────── Laden ──────────────────

    def _kategorien_laden(self):
        """Kategorie-Buttons neu aufbauen."""
        for w in self._tab_frame.winfo_children():
            w.destroy()

        kategorien = alle_kategorien()
        if not kategorien:
            tk.Label(
                self._tab_frame,
                text="Noch keine Kategorien – über ⚙ Verwalten anlegen",
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                bg=COLOR_BG, fg=COLOR_SUBTEXT
            ).pack(side="left")
            self._produkte_laden(None)
            return

        for kat in kategorien:
            is_aktiv = kat["id"] == self._aktive_kategorie_id
            btn = tk.Button(
                self._tab_frame,
                text=kat["name"],
                font=(FONT_FAMILY, FONT_SIZE_SMALL,
                      "bold" if is_aktiv else "normal"),
                bg=COLOR_ACCENT if is_aktiv else COLOR_SURFACE,
                fg=COLOR_BG if is_aktiv else COLOR_TEXT,
                activebackground=COLOR_ACCENT,
                activeforeground=COLOR_BG,
                relief="flat", cursor="hand2",
                padx=14, pady=6,
                command=lambda k=kat: self._kategorie_select(k["id"])
            )
            btn.pack(side="left", padx=(0, 6))

        # Erste Kategorie vorauswählen falls noch nichts aktiv
        if self._aktive_kategorie_id is None and kategorien:
            self._kategorie_select(kategorien[0]["id"])
        else:
            self._produkte_laden(self._aktive_kategorie_id)

    def _kategorie_select(self, kategorie_id: int):
        self._aktive_kategorie_id = kategorie_id
        self._kategorien_laden()

    def _produkte_laden(self, kategorie_id):
        """Produktkarten im Grid neu aufbauen."""
        for w in self._produkt_grid.winfo_children():
            w.destroy()

        if kategorie_id is None:
            return

        produkte = produkte_der_kategorie(kategorie_id)
        if not produkte:
            tk.Label(
                self._produkt_grid,
                text="Keine Produkte in dieser Kategorie.",
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                bg=COLOR_BG, fg=COLOR_SUBTEXT
            ).grid(row=0, column=0, padx=10, pady=20)
            return

        cols = 3
        for i, prod in enumerate(produkte):
            row, col = divmod(i, cols)
            self._produkt_karte(self._produkt_grid, prod, row, col)

        for c in range(cols):
            self._produkt_grid.columnconfigure(c, weight=1)

    def _produkt_karte(self, parent, prod: dict, row: int, col: int):
        """Einzelne Touch-freundliche Produktkarte."""
        card = tk.Frame(
            parent, bg=COLOR_SURFACE,
            relief="flat", bd=0
        )
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        # Klick auf Kartenbereich → Produkt zum Warenkorb hinzufügen
        def on_click(e=None):
            if self._on_produkt_clicked:
                self._on_produkt_clicked(prod)

        for widget in [card]:
            widget.bind("<Button-1>", on_click)

        # Name
        name_lbl = tk.Label(
            card, text=prod["name"],
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_SURFACE, fg=COLOR_TEXT,
            wraplength=160, justify="center", cursor="hand2"
        )
        name_lbl.pack(pady=(16, 4), padx=12)
        name_lbl.bind("<Button-1>", on_click)

        # Preis
        preis_lbl = tk.Label(
            card,
            text=f"{prod['preis']:.2f} €",
            font=(FONT_FAMILY, FONT_SIZE_TITLE),
            bg=COLOR_SURFACE, fg=COLOR_ACCENT, cursor="hand2"
        )
        preis_lbl.pack(pady=(0, 12))
        preis_lbl.bind("<Button-1>", on_click)

        # Bearbeiten-Button (mit Passwort)
        tk.Button(
            card, text="✏",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_SURFACE, fg=COLOR_SUBTEXT,
            activebackground=COLOR_SURFACE,
            relief="flat", cursor="hand2",
            command=lambda p=prod: self._produkt_bearbeiten_dialog(p)
        ).pack(side="right", padx=6, pady=(0, 8))

    # ─────────────────────────────────────────────── Dialoge ────────────────

    def _verwaltung_oeffnen(self):
        """Öffnet ein Verwaltungsfenster für Kategorien und Produkte anlegen."""
        if not passwort_pruefen(self):
            return
        VerwaltungsDialog(self, on_close=self._nach_verwaltung)

    def _nach_verwaltung(self):
        self._kategorien_laden()

    def _produkt_bearbeiten_dialog(self, prod: dict):
        if not passwort_pruefen(self):
            return
        ProduktBearbeitenDialog(self, prod, on_close=lambda: self._produkte_laden(self._aktive_kategorie_id))

    def refresh(self):
        self._kategorien_laden()


# ─────────────────────────────────────── Verwaltungs-Dialog ─────────────────


class VerwaltungsDialog(tk.Toplevel):
    """Dialog: Kategorien + Produkte anlegen/löschen."""

    def __init__(self, parent, on_close=None):
        super().__init__(parent)
        self._on_close = on_close
        self.title("Produkte & Kategorien verwalten")
        self.configure(bg=COLOR_BG)
        self.geometry("520x580")
        self.grab_set()
        self._build()

    def _build(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=16)

        # ── Tab: Kategorien ──────────────────────────────────────────────────
        kat_frame = tk.Frame(nb, bg=COLOR_BG)
        nb.add(kat_frame, text="  Kategorien  ")
        self._build_kategorien_tab(kat_frame)

        # ── Tab: Produkt anlegen ─────────────────────────────────────────────
        prod_frame = tk.Frame(nb, bg=COLOR_BG)
        nb.add(prod_frame, text="  Produkt anlegen  ")
        self._build_produkt_tab(prod_frame)

        tk.Button(
            self, text="Schließen",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=COLOR_ACCENT, fg=COLOR_BG,
            relief="flat", cursor="hand2",
            padx=20, pady=6,
            command=self._schliessen
        ).pack(pady=10)

    # ── Kategorien-Tab ───────────────────────────────────────────────────────

    def _build_kategorien_tab(self, parent):
        tk.Label(parent, text="Neue Kategorie",
                 font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor="w", padx=16, pady=(16, 4))

        row = tk.Frame(parent, bg=COLOR_BG)
        row.pack(fill="x", padx=16)

        self._kat_name_var = tk.StringVar()
        tk.Entry(row, textvariable=self._kat_name_var,
                 font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                 bg=COLOR_SURFACE, fg=COLOR_TEXT,
                 insertbackground=COLOR_TEXT,
                 relief="flat", bd=8
                 ).pack(side="left", fill="x", expand=True)

        tk.Button(row, text="＋",
                  font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                  bg=COLOR_ACCENT, fg=COLOR_BG,
                  relief="flat", cursor="hand2", padx=10,
                  command=self._kategorie_anlegen
                  ).pack(side="left", padx=(8, 0))

        self._kat_status = tk.StringVar()
        tk.Label(parent, textvariable=self._kat_status,
                 font=(FONT_FAMILY, FONT_SIZE_SMALL),
                 bg=COLOR_BG, fg=COLOR_GREEN).pack(anchor="w", padx=16)

        tk.Label(parent, text="Vorhandene Kategorien",
                 font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor="w", padx=16, pady=(16, 4))

        self._kat_listbox = tk.Listbox(
            parent, font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=COLOR_SURFACE, fg=COLOR_TEXT,
            selectbackground=COLOR_ACCENT, selectforeground=COLOR_BG,
            relief="flat", bd=0, height=6
        )
        self._kat_listbox.pack(fill="x", padx=16)
        self._kat_ids = []
        self._kat_liste_laden()

        tk.Button(parent, text="Ausgewählte Kategorie löschen",
                  font=(FONT_FAMILY, FONT_SIZE_SMALL),
                  bg=COLOR_RED, fg=COLOR_BG,
                  relief="flat", cursor="hand2", padx=10, pady=4,
                  command=self._kategorie_loeschen
                  ).pack(anchor="w", padx=16, pady=8)

    def _kat_liste_laden(self):
        self._kat_listbox.delete(0, tk.END)
        self._kat_ids.clear()
        for k in alle_kategorien():
            self._kat_listbox.insert(tk.END, k["name"])
            self._kat_ids.append(k["id"])

    def _kategorie_anlegen(self):
        try:
            kategorie_anlegen(self._kat_name_var.get())
            self._kat_name_var.set("")
            self._kat_status.set("✓ Kategorie angelegt.")
            self._kat_liste_laden()
        except KategorieError as e:
            self._kat_status.set(str(e))

    def _kategorie_loeschen(self):
        sel = self._kat_listbox.curselection()
        if not sel:
            return
        try:
            kategorie_loeschen(self._kat_ids[sel[0]])
            self._kat_status.set("✓ Kategorie gelöscht.")
            self._kat_liste_laden()
        except KategorieError as e:
            self._kat_status.set(str(e))

    # ── Produkt-Tab ──────────────────────────────────────────────────────────

    def _build_produkt_tab(self, parent):
        def label(text):
            tk.Label(parent, text=text,
                     font=(FONT_FAMILY, FONT_SIZE_SMALL),
                     bg=COLOR_BG, fg=COLOR_SUBTEXT
                     ).pack(anchor="w", padx=16, pady=(10, 2))

        def entry(var):
            e = tk.Entry(parent, textvariable=var,
                         font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                         bg=COLOR_SURFACE, fg=COLOR_TEXT,
                         insertbackground=COLOR_TEXT,
                         relief="flat", bd=8)
            e.pack(fill="x", padx=16)
            return e

        label("Produktname *")
        self._prod_name_var = tk.StringVar()
        entry(self._prod_name_var)

        label("Preis (€) *")
        self._prod_preis_var = tk.StringVar()
        entry(self._prod_preis_var)

        label("Kategorie *")
        self._prod_kat_var = tk.StringVar()
        self._prod_kat_dropdown = tk.OptionMenu(parent, self._prod_kat_var, "")
        self._prod_kat_dropdown.config(
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=COLOR_SURFACE, fg=COLOR_TEXT,
            activebackground=COLOR_ACCENT, activeforeground=COLOR_BG,
            relief="flat", bd=0, highlightthickness=0, anchor="w"
        )
        self._prod_kat_dropdown.pack(fill="x", padx=16, pady=(0, 4))
        self._prod_kat_ids = {}
        self._prod_kat_liste_laden()

        self._prod_status = tk.StringVar()
        tk.Label(parent, textvariable=self._prod_status,
                 font=(FONT_FAMILY, FONT_SIZE_SMALL),
                 bg=COLOR_BG, fg=COLOR_GREEN, wraplength=400,
                 ).pack(anchor="w", padx=16, pady=4)

        tk.Button(parent, text="＋  Produkt anlegen",
                  font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                  bg=COLOR_ACCENT, fg=COLOR_BG,
                  relief="flat", cursor="hand2", height=BUTTON_HEIGHT,
                  command=self._produkt_anlegen
                  ).pack(fill="x", padx=16, pady=8)

    def _prod_kat_liste_laden(self):
        menu = self._prod_kat_dropdown["menu"]
        menu.delete(0, "end")
        self._prod_kat_ids.clear()
        for k in alle_kategorien():
            self._prod_kat_ids[k["name"]] = k["id"]
            menu.add_command(
                label=k["name"],
                command=lambda n=k["name"]: self._prod_kat_var.set(n)
            )
        if self._prod_kat_ids:
            self._prod_kat_var.set(next(iter(self._prod_kat_ids)))

    def _produkt_anlegen(self):
        try:
            preis = float(self._prod_preis_var.get().replace(",", "."))
            kat_name = self._prod_kat_var.get()
            kat_id = self._prod_kat_ids.get(kat_name)
            produkt_anlegen(self._prod_name_var.get(), preis, kat_id)
            self._prod_name_var.set("")
            self._prod_preis_var.set("")
            self._prod_status.set("✓ Produkt angelegt.")
        except (ValueError, TypeError):
            self._prod_status.set("Ungültiger Preis. Bitte Zahl eingeben.")
        except ProduktError as e:
            self._prod_status.set(str(e))

    def _schliessen(self):
        self.destroy()
        if self._on_close:
            self._on_close()


# ─────────────────────────────────── Produkt bearbeiten ─────────────────────

class ProduktBearbeitenDialog(tk.Toplevel):
    def __init__(self, parent, prod: dict, on_close=None):
        super().__init__(parent)
        self._prod = prod
        self._on_close = on_close
        self.title(f"Produkt bearbeiten: {prod['name']}")
        self.configure(bg=COLOR_BG)
        self.geometry("400x360")
        self.grab_set()
        self._build()

    def _build(self):
        tk.Label(self, text="Produkt bearbeiten",
                 font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
                 bg=COLOR_BG, fg=COLOR_ACCENT).pack(pady=(20, 4))

        tk.Frame(self, height=1, bg=COLOR_BORDER).pack(fill="x", padx=20, pady=8)

        form = tk.Frame(self, bg=COLOR_BG)
        form.pack(fill="x", padx=20)

        def label(parent, text):
            tk.Label(parent, text=text,
                     font=(FONT_FAMILY, FONT_SIZE_SMALL),
                     bg=COLOR_BG, fg=COLOR_SUBTEXT
                     ).pack(anchor="w", pady=(8, 2))

        def entry(parent, var):
            tk.Entry(parent, textvariable=var,
                     font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                     bg=COLOR_SURFACE, fg=COLOR_TEXT,
                     insertbackground=COLOR_TEXT,
                     relief="flat", bd=8
                     ).pack(fill="x")

        label(form, "Produktname *")
        self._name_var = tk.StringVar(value=self._prod["name"])
        entry(form, self._name_var)

        label(form, "Preis (€) *")
        self._preis_var = tk.StringVar(value=f"{self._prod['preis']:.2f}")
        entry(form, self._preis_var)

        label(form, "Kategorie *")
        self._kat_var = tk.StringVar(value=self._prod["kategorie"])
        self._kat_ids = {}
        self._kat_dropdown = tk.OptionMenu(form, self._kat_var, "")
        self._kat_dropdown.config(
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=COLOR_SURFACE, fg=COLOR_TEXT,
            activebackground=COLOR_ACCENT, activeforeground=COLOR_BG,
            relief="flat", bd=0, highlightthickness=0, anchor="w"
        )
        self._kat_dropdown.pack(fill="x")
        self._kat_liste_laden()

        self._status_var = tk.StringVar()
        tk.Label(self, textvariable=self._status_var,
                 font=(FONT_FAMILY, FONT_SIZE_SMALL),
                 bg=COLOR_BG, fg=COLOR_GREEN).pack(pady=(8, 0))

        btn_row = tk.Frame(self, bg=COLOR_BG)
        btn_row.pack(pady=12)

        tk.Button(btn_row, text="🗑  Löschen",
                  font=(FONT_FAMILY, FONT_SIZE_SMALL),
                  bg=COLOR_RED, fg=COLOR_BG,
                  relief="flat", cursor="hand2", padx=12, pady=6,
                  command=self._loeschen).pack(side="left", padx=6)

        tk.Button(btn_row, text="💾  Speichern",
                  font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                  bg=COLOR_ACCENT, fg=COLOR_BG,
                  relief="flat", cursor="hand2", padx=12, pady=6,
                  command=self._speichern).pack(side="left", padx=6)

    def _kat_liste_laden(self):
        menu = self._kat_dropdown["menu"]
        menu.delete(0, "end")
        for k in alle_kategorien():
            self._kat_ids[k["name"]] = k["id"]
            menu.add_command(
                label=k["name"],
                command=lambda n=k["name"]: self._kat_var.set(n)
            )

    def _speichern(self):
        try:
            preis = float(self._preis_var.get().replace(",", "."))
            kat_id = self._kat_ids.get(self._kat_var.get())
            produkt_bearbeiten(self._prod["id"], self._name_var.get(), preis, kat_id)
            self._status_var.set("✓ Gespeichert.")
            self.after(800, self._schliessen)
        except (ValueError, TypeError):
            self._status_var.set("Ungültiger Preis.")
        except ProduktError as e:
            self._status_var.set(str(e))

    def _loeschen(self):
        produkt_loeschen(self._prod["id"])
        self._schliessen()

    def _schliessen(self):
        self.destroy()
        if self._on_close:
            self._on_close()
