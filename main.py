"""
SVM Kantine – Kassensystem
Einstiegspunkt: initialisiert die Datenbank und startet die GUI.
"""

import tkinter as tk
from database import init_db
from src.ui.main_window import MainWindow


def main():
    init_db()
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
