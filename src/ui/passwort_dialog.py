"""
Kassensystem – Wiederverwendbarer Passwort-Dialog
"""

import tkinter as tk
from tkinter import simpledialog
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config import (
    FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_SMALL,
    COLOR_BG, COLOR_SURFACE, COLOR_ACCENT, COLOR_RED,
    COLOR_TEXT, COLOR_SUBTEXT, COLOR_BORDER, PRODUKT_PASSWORT
)


def passwort_pruefen(parent: tk.Widget, passwort: str = None) -> bool:
    """
    Öffnet einen modalen Passwort-Dialog.
    Gibt True zurück, wenn das eingegebene Passwort korrekt ist.
    """
    if passwort is None:
        passwort = PRODUKT_PASSWORT

    dialog = _PasswortDialog(parent, passwort)
    return dialog.result


class _PasswortDialog(tk.Toplevel):
    def __init__(self, parent, expected_pw: str):
        super().__init__(parent)
        self.result = False
        self._expected = expected_pw

        self.title("Passwort erforderlich")
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self.grab_set()  # Modal

        # Zentrieren relativ zum Parent-Fenster
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width() // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2
        self.geometry(f"360x200+{px - 180}+{py - 100}")

        self._build()
        self.wait_window()

    def _build(self):
        tk.Label(
            self, text="🔒  Passwort eingeben",
            font=(FONT_FAMILY, 15, "bold"),
            bg=COLOR_BG, fg=COLOR_ACCENT
        ).pack(pady=(20, 4))

        tk.Label(
            self,
            text="Für diese Aktion ist ein Passwort erforderlich.",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_BG, fg=COLOR_SUBTEXT
        ).pack()

        self._pw_var = tk.StringVar()
        entry = tk.Entry(
            self, textvariable=self._pw_var,
            show="•",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=COLOR_SURFACE, fg=COLOR_TEXT,
            insertbackground=COLOR_TEXT,
            relief="flat", bd=8, width=22,
        )
        entry.pack(pady=14)
        entry.focus_set()
        entry.bind("<Return>", lambda e: self._bestaetigen())

        self._error_var = tk.StringVar()
        tk.Label(
            self, textvariable=self._error_var,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_BG, fg=COLOR_RED
        ).pack()

        btn_frame = tk.Frame(self, bg=COLOR_BG)
        btn_frame.pack(pady=8)

        tk.Button(
            btn_frame, text="Abbrechen",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_SURFACE, fg=COLOR_SUBTEXT,
            activebackground=COLOR_SURFACE,
            relief="flat", cursor="hand2", padx=16, pady=6,
            command=self.destroy
        ).pack(side="left", padx=6)

        tk.Button(
            btn_frame, text="Bestätigen",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=COLOR_ACCENT, fg=COLOR_BG,
            activebackground=COLOR_ACCENT,
            relief="flat", cursor="hand2", padx=16, pady=6,
            command=self._bestaetigen
        ).pack(side="left", padx=6)

    def _bestaetigen(self):
        if self._pw_var.get() == self._expected:
            self.result = True
            self.destroy()
        else:
            self._error_var.set("Falsches Passwort. Bitte erneut versuchen.")
            self._pw_var.set("")
