"""
Kassensystem – Hauptfenster
Links: PersonenView + BestellView (Sidebar)
Rechts: Tab-Navigation → Bestellung | Offene Beträge | Statistiken
"""

import tkinter as tk
from tkinter import ttk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config import (
    APP_TITLE, FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_SMALL,
    COLOR_BG, COLOR_SIDEBAR, COLOR_SURFACE, COLOR_TEXT, COLOR_SUBTEXT,
    COLOR_BORDER, COLOR_ACCENT, COLOR_GREEN
)
from src.ui.personen_view import PersonenView
from src.ui.produkt_view import ProduktView
from src.ui.bestell_view import BestellView
from src.ui.dashboard_view import DashboardView
from src.ui.statistik_view import StatistikView


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._aktive_person = None
        self._setup_window()
        self._build_layout()

    def _setup_window(self):
        self.root.title(APP_TITLE)
        self.root.configure(bg=COLOR_BG)
        self.root.geometry("1200x800")
        self.root.minsize(900, 640)

    def _build_layout(self):
        container = tk.Frame(self.root, bg=COLOR_BG)
        container.pack(fill="both", expand=True)

        # ── Linke Sidebar ───────────────────────────────────────────────────
        sidebar = tk.Frame(container, bg=COLOR_SIDEBAR, width=300)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        self._personen_view = PersonenView(
            sidebar, on_person_selected=self._on_person_selected
        )
        self._personen_view.pack(fill="x")

        self._bestell_view = BestellView(
            sidebar, on_abgeschlossen=self._on_bestellung_abgeschlossen
        )
        self._bestell_view.pack(fill="both", expand=True)

        # ── Trennlinie ──────────────────────────────────────────────────────
        tk.Frame(container, width=1, bg=COLOR_BORDER).pack(side="left", fill="y")

        # ── Rechter Bereich mit Tab-Navigation ──────────────────────────────
        right = tk.Frame(container, bg=COLOR_BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_tab_navigation(right)

    def _build_tab_navigation(self, parent: tk.Frame):
        """Eigene Tab-Leiste (Bestellung | Offene Beträge | Statistiken)."""
        # Tab-Schaltflächen oben
        tab_bar = tk.Frame(parent, bg=COLOR_BG)
        tab_bar.pack(fill="x", padx=20, pady=(12, 0))

        self._tab_buttons = {}
        self._tab_frames = {}
        tabs = [
            ("bestellung", "🛒  Bestellung"),
            ("dashboard", "📋  Offene Beträge"),
            ("statistik", "📊  Statistiken"),
        ]

        for key, label in tabs:
            btn = tk.Button(
                tab_bar, text=label,
                font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
                relief="flat", cursor="hand2",
                padx=16, pady=8,
                command=lambda k=key: self._tab_select(k)
            )
            btn.pack(side="left", padx=(0, 4))
            self._tab_buttons[key] = btn

        tk.Frame(parent, height=1, bg=COLOR_BORDER).pack(
            fill="x", padx=20, pady=(8, 0)
        )

        # Tab-Inhalte
        content = tk.Frame(parent, bg=COLOR_BG)
        content.pack(fill="both", expand=True)

        self._produkt_view = ProduktView(
            content, on_produkt_clicked=self._on_produkt_clicked
        )
        self._tab_frames["bestellung"] = self._produkt_view

        self._dashboard_view = DashboardView(content)
        self._tab_frames["dashboard"] = self._dashboard_view

        self._statistik_view = StatistikView(content)
        self._tab_frames["statistik"] = self._statistik_view

        # Starttab
        self._aktiver_tab = None
        self._tab_select("bestellung")

    def _tab_select(self, key: str):
        if self._aktiver_tab == key:
            return
        self._aktiver_tab = key

        # Frames ein-/ausblenden
        for k, frame in self._tab_frames.items():
            if k == key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

        # Button-Styling
        for k, btn in self._tab_buttons.items():
            active = k == key
            btn.config(
                bg=COLOR_ACCENT if active else COLOR_SURFACE,
                fg=COLOR_BG if active else COLOR_TEXT,
            )

        # Views beim Wechsel aktualisieren
        if key == "dashboard":
            self._dashboard_view._laden()
        elif key == "statistik":
            self._statistik_view.refresh()

    # ──────────────────────────────────────────────── Callbacks ─────────────

    def _on_person_selected(self, person: dict | None):
        self._aktive_person = person
        self._bestell_view.set_person(person)

    def _on_produkt_clicked(self, produkt: dict):
        if not self._aktive_person:
            self._personen_view._set_status(
                "⚠ Bitte zuerst eine Person auswählen!", error=True
            )
            return
        self._bestell_view.produkt_hinzufuegen(produkt)

    def _on_bestellung_abgeschlossen(self, gesamt: float):
        self._zeige_toast(f"✓  Bestellung abgeschlossen  –  {gesamt:.2f} €", COLOR_GREEN)

    def _zeige_toast(self, text: str, bg: str):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.configure(bg=bg)
        self.root.update_idletasks()
        x = self.root.winfo_rootx() + self.root.winfo_width() - 360
        y = self.root.winfo_rooty() + 20
        toast.geometry(f"340x58+{x}+{y}")
        tk.Label(
            toast, text=text,
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
            bg=bg, fg=COLOR_BG, pady=18
        ).pack(fill="both", expand=True)
        toast.after(2500, toast.destroy)
