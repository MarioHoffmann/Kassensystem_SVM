/* ─── bestellung.js – Warenkorb & Bestellungsmanagement ─── */

async function ladeBestellung(personId) {
    try {
        const data = await api("GET", `/bestellungen/aktiv/${personId}`);
        state.bestellungId = data.id;
        renderWarenkorb(data.positionen, data.gesamt);
    } catch (e) {
        showToast(e.message, true);
    }
}

function ladeWarenkorb() {
    if (!state.person) {
        document.getElementById("warenkorb-liste").innerHTML =
            '<p class="empty-hint">Keine Person ausgewählt.</p>';
        document.getElementById("warenkorb-footer").style.display = "none";
        document.getElementById("warenkorb-titel").textContent = "Bestellung";
        return;
    }
    ladeBestellung(state.person.id);
}

function renderWarenkorb(positionen, gesamt) {
    const liste = document.getElementById("warenkorb-liste");
    const footer = document.getElementById("warenkorb-footer");

    if (!positionen || positionen.length === 0) {
        liste.innerHTML = '<p class="empty-hint">Noch keine Produkte.</p>';
        footer.style.display = "none";
        return;
    }

    liste.innerHTML = "";
    positionen.forEach(pos => {
        const item = document.createElement("div");
        item.className = "warenkorb-item";
        item.innerHTML = `
          <div class="warenkorb-menge">
            <button class="menge-btn minus-btn" data-id="${pos.id}" data-delta="-1" title="Weniger">−</button>
            <span class="menge-zahl">${pos.menge}</span>
            <button class="menge-btn plus-btn"  data-id="${pos.id}" data-delta="1"  title="Mehr">+</button>
          </div>
          <div class="warenkorb-info">
            <div class="warenkorb-produkt">${pos.produkt_name}</div>
            <div class="warenkorb-einzelpreis">${eur(pos.einzelpreis)} / Stk</div>
          </div>
          <div class="warenkorb-right">
            <div class="warenkorb-gesamtpreis">${eur(pos.menge * pos.einzelpreis)}</div>
            <button class="warenkorb-del-btn" data-id="${pos.id}" title="Entfernen">✕</button>
          </div>
        `;
        liste.appendChild(item);
    });

    // +/− Buttons
    liste.querySelectorAll(".menge-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
            const id = parseInt(btn.dataset.id);
            const delta = parseInt(btn.dataset.delta);
            try {
                await api("PATCH", `/bestellungen/positionen/${id}`, { delta });
                await ladeBestellung(state.person.id);
            } catch (e) { showToast(e.message, true); }
        });
    });

    // ✕ Direkt-Löschen pro Position
    liste.querySelectorAll(".warenkorb-del-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
            const id = parseInt(btn.dataset.id);
            try {
                await api("DELETE", `/bestellungen/positionen/${id}`);
                await ladeBestellung(state.person.id);
            } catch (e) { showToast(e.message, true); }
        });
    });

    footer.style.display = "";
    document.getElementById("gesamt-preis").textContent = eur(gesamt);
}

async function addProduktZuBestellung(p) {
    if (!state.bestellungId) return;
    try {
        const data = await api("POST", `/bestellungen/${state.bestellungId}/produkt`, {
            produkt_id: p.id,
            einzelpreis: p.preis,
        });
        renderWarenkorb(data.positionen, data.gesamt);
    } catch (e) { showToast(e.message, true); }
}

// Bestellung abschließen
document.getElementById("btn-abschliessen").addEventListener("click", async () => {
    if (!state.bestellungId) return;
    try {
        const res = await api("POST", `/bestellungen/${state.bestellungId}/abschliessen`);
        showToast(`✓ Bestellung fertig – ${eur(res.gesamt)}`);
        state.bestellungId = null;
        await ladeBestellung(state.person.id);
    } catch (e) { showToast(e.message, true); }
});

// Polling: alle 5 Sekunden Warenkorb neu laden (Multi-Device-Sync)
setInterval(() => {
    if (state.person && state.bestellungId) ladeBestellung(state.person.id);
}, 5000);
