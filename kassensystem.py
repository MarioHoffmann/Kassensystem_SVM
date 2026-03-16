import tkinter as tk
from tkinter import ttk, messagebox

# Hauptfenster erstellen
class Kassensystem:
    def __init__(self, root):
        self.root = root
        self.root.title("SVM Kantine")

        # Datenstrukturen für Kunden und Produkte
        self.kunden = {}
        self.produkte = {}
        self.warenkorb = []

        # Tabs erstellen
        self.tab_control = ttk.Notebook(root)
        self.kunden_tab = ttk.Frame(self.tab_control)
        self.produkte_tab = ttk.Frame(self.tab_control)
        self.bestellung_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.kunden_tab, text="Kundenverwaltung")
        self.tab_control.add(self.produkte_tab, text="Produktverwaltung")
        self.tab_control.add(self.bestellung_tab, text="Bestellung")

        self.tab_control.pack(expand=1, fill="both")

        self.create_kunden_tab()
        self.create_produkte_tab()
        self.create_bestellung_tab()

    # Kundenverwaltung
    def create_kunden_tab(self):
        ttk.Label(self.kunden_tab, text="Kundenverwaltung", font=("Arial", 16)).pack(pady=10)

        self.kunden_name_var = tk.StringVar()
        ttk.Label(self.kunden_tab, text="Name:").pack(pady=5)
        ttk.Entry(self.kunden_tab, textvariable=self.kunden_name_var).pack(pady=5)

        ttk.Button(self.kunden_tab, text="Kunden hinzufügen", command=self.add_kunde).pack(pady=5)
        self.kunden_listbox = tk.Listbox(self.kunden_tab, height=10, width=40)
        self.kunden_listbox.pack(pady=10)

    def add_kunde(self):
        name = self.kunden_name_var.get()
        if not name:
            messagebox.showerror("Fehler", "Name darf nicht leer sein!")
            return
        if name in self.kunden:
            messagebox.showerror("Fehler", "Kunde existiert bereits!")
            return
        self.kunden[name] = []
        self.kunden_listbox.insert(tk.END, name)
        self.kunden_name_var.set("")

    # Produktverwaltung
    def create_produkte_tab(self):
        ttk.Label(self.produkte_tab, text="Produktverwaltung", font=("Arial", 16)).pack(pady=10)

        self.produkt_name_var = tk.StringVar()
        self.produkt_preis_var = tk.DoubleVar()

        ttk.Label(self.produkte_tab, text="Produktname:").pack(pady=5)
        ttk.Entry(self.produkte_tab, textvariable=self.produkt_name_var).pack(pady=5)

        ttk.Label(self.produkte_tab, text="Preis:").pack(pady=5)
        ttk.Entry(self.produkte_tab, textvariable=self.produkt_preis_var).pack(pady=5)

        ttk.Button(self.produkte_tab, text="Produkt hinzufügen", command=self.add_produkt).pack(pady=5)
        self.produkte_listbox = tk.Listbox(self.produkte_tab, height=10, width=40)
        self.produkte_listbox.pack(pady=10)

    def add_produkt(self):
        name = self.produkt_name_var.get()
        preis = self.produkt_preis_var.get()
        if not name or preis <= 0:
            messagebox.showerror("Fehler", "Ungültige Eingabe!")
            return
        if name in self.produkte:
            messagebox.showerror("Fehler", "Produkt existiert bereits!")
            return
        self.produkte[name] = preis
        self.produkte_listbox.insert(tk.END, f"{name} - {preis:.2f} €")
        self.produkt_name_var.set("")
        self.produkt_preis_var.set(0.0)

    # Bestellung
    def create_bestellung_tab(self):
        ttk.Label(self.bestellung_tab, text="Bestellung", font=("Arial", 16)).pack(pady=10)

        self.bestellung_listbox = tk.Listbox(self.bestellung_tab, height=10, width=40)
        self.bestellung_listbox.pack(pady=10)

        ttk.Button(self.bestellung_tab, text="Produkt hinzufügen", command=self.add_to_cart).pack(pady=5)
        ttk.Button(self.bestellung_tab, text="Bestellung abschließen", command=self.complete_order).pack(pady=5)

    def add_to_cart(self):
        selected = self.produkte_listbox.curselection()
        if not selected:
            messagebox.showerror("Fehler", "Kein Produkt ausgewählt!")
            return
        produkt = list(self.produkte.keys())[selected[0]]
        self.warenkorb.append(produkt)
        self.bestellung_listbox.insert(tk.END, produkt)

    def complete_order(self):
        if not self.warenkorb:
            messagebox.showerror("Fehler", "Warenkorb ist leer!")
            return
        gesamtpreis = sum(self.produkte[produkt] for produkt in self.warenkorb)
        messagebox.showinfo("Bestellung abgeschlossen", f"Gesamtpreis: {gesamtpreis:.2f} €")
        self.warenkorb.clear()
        self.bestellung_listbox.delete(0, tk.END)

# Anwendung starten
if __name__ == "__main__":
    root = tk.Tk()
    app = Kassensystem(root)
    root.mainloop()
