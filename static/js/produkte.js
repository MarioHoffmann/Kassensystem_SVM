/* ─── produkte.js – Kategorien & Produktverwaltung ─── */

let _editProduktId = null;

// ── Kategorien & Produkte laden ───────────────────────────────────────────────
async function ladeKategorienUndProdukte() {
    const kats = await api("GET", "/produkte/kategorien");
    const bar = document.getElementById("kategorie-tabs");
    bar.innerHTML = "";

    if (kats.length === 0) {
        document.getElementById("produkt-grid").innerHTML =
            '<p class="empty-hint centered">Keine Kategorien – oben "+ Kategorie" klicken.</p>';
        return;
    }

    if (!state.katId || !kats.find(k => k.id === state.katId)) {
        state.katId = kats[0].id;
    }

    kats.forEach(k => {
        const btn = document.createElement("button");
        btn.className = "kat-tab" + (k.id === state.katId ? " active" : "");
        btn.dataset.kid = k.id;

        // Text + Edit-Icon falls aktiv
        if (k.id === state.katId) {
            btn.innerHTML = `<span>${k.name}</span> <span class="kat-edit-icon" title="Kategorie bearbeiten">✎</span>`;
            btn.querySelector(".kat-edit-icon").addEventListener("click", (e) => {
                e.stopPropagation();
                oeffneKategorieEditModal(k);
            });
        } else {
            btn.textContent = k.name;
        }

        btn.addEventListener("click", () => {
            if (state.sortMode) return;
            waehleKategorie(k.id);
        });

        if (state.sortMode) {
            btn.draggable = true;
            makeElementSortable(btn, speichereKategorienReihenfolge);
        }

        bar.appendChild(btn);
    });

    ladeProdukte(state.katId);
}

function waehleKategorie(kid) {
    state.katId = kid;
    ladeKategorienUndProdukte(); // Komplett neu laden um Edit-Icon zu verschieben
}

async function ladeProdukte(kid) {
    const grid = document.getElementById("produkt-grid");
    grid.innerHTML = "";
    const produkte = await api("GET", `/produkte/?kategorie_id=${kid}`);

    produkte.forEach(p => {
        const card = document.createElement("div");
        card.className = "produkt-karte";
        card.dataset.pid = p.id;
        card.innerHTML = `
          <span class="produkt-name">${p.name}</span>
          <span class="produkt-preis">${eur(p.preis)}</span>
          <button class="produkt-edit-btn" title="Bearbeiten">✎</button>
        `;
        card.querySelector(".produkt-edit-btn").addEventListener("click", (e) => {
            e.stopPropagation();
            oeffneProduktEditModal(p);
        });
        card.addEventListener("click", () => {
            if (state.sortMode) return;
            produktGeklickt(p);
        });

        if (state.sortMode) {
            card.draggable = true;
            makeElementSortable(card, speichereProdukteReihenfolge);
        }

        grid.appendChild(card);
    });

    // + Produkt hinzufügen
    const addBtn = document.createElement("div");
    addBtn.className = "produkt-karte add-produkt-btn";
    addBtn.innerHTML = `<span style="font-size:28px">+</span><span class="produkt-name" style="color:var(--subtext)">Produkt</span>`;
    addBtn.addEventListener("click", () => {
        if (state.sortMode) return;
        oeffneNeuesProduktModal();
    });
    grid.appendChild(addBtn);
}

function produktGeklickt(p) {
    if (!state.person) {
        showToast("⚠ Zuerst eine Person auswählen!", true);
        return;
    }
    addProduktZuBestellung(p);
}

// ── Produkt-Modals ────────────────────────────────────────────────────────────

function _zeigeProduktModal(titel, name, preis, mitLoeschBtn) {
    document.getElementById("modal-prod-titel").textContent = titel;
    document.getElementById("modal-prod-name").value = name;
    document.getElementById("modal-prod-preis").value = preis;
    document.getElementById("modal-prod-error").textContent = "";
    const loeschBtn = document.getElementById("modal-prod-loeschen");
    loeschBtn.style.display = mitLoeschBtn ? "" : "none";
    loeschBtn.textContent = "🗑 Produkt löschen";
    delete loeschBtn.dataset.confirm;
    openModal("modal-produkt");
    setTimeout(() => document.getElementById("modal-prod-name").focus(), 50);
}

async function oeffneNeuesProduktModal() {
    if (!await checkPasswort()) return;
    _editProduktId = null;
    _zeigeProduktModal("Neues Produkt", "", "", false);
}

async function oeffneProduktEditModal(p) {
    if (!await checkPasswort()) return;
    _editProduktId = p.id;
    _zeigeProduktModal("Produkt bearbeiten", p.name, p.preis.toFixed(2), true);
}

// Produkt speichern (statischer Listener)
document.getElementById("modal-prod-ok").addEventListener("click", async () => {
    const name = document.getElementById("modal-prod-name").value.trim();
    const preis = parseFloat(document.getElementById("modal-prod-preis").value.replace(",", "."));
    const err = document.getElementById("modal-prod-error");

    if (!name) { err.textContent = "Bitte einen Produktnamen eingeben."; return; }
    if (isNaN(preis) || preis < 0) { err.textContent = "Bitte einen gültigen Preis eingeben (0 ist erlaubt)."; return; }
    err.textContent = "";

    try {
        if (_editProduktId) {
            await api("PUT", `/produkte/${_editProduktId}`, { name, preis, kategorie_id: state.katId });
            showToast(`✓ "${name}" aktualisiert.`);
        } else {
            await api("POST", "/produkte/", { name, preis, kategorie_id: state.katId });
            showToast(`✓ "${name}" angelegt.`);
        }
        closeModal();
        ladeProdukte(state.katId);
    } catch (e) { err.textContent = e.message; }
});

// Produkt löschen – Double-Tap-Bestätigung (statischer Listener)
document.getElementById("modal-prod-loeschen").addEventListener("click", async () => {
    if (!_editProduktId) return;
    const btn = document.getElementById("modal-prod-loeschen");
    const name = document.getElementById("modal-prod-name").value.trim();

    if (btn.dataset.confirm !== "1") {
        btn.textContent = "⚠ Nochmal antippen zum Löschen";
        btn.dataset.confirm = "1";
        setTimeout(() => {
            if (btn.dataset.confirm === "1") {
                btn.textContent = "🗑 Produkt löschen";
                delete btn.dataset.confirm;
            }
        }, 3000);
        return;
    }
    delete btn.dataset.confirm;
    try {
        await api("DELETE", `/produkte/${_editProduktId}`);
        closeModal();
        ladeProdukte(state.katId);
        showToast(`🗑 "${name}" gelöscht.`);
    } catch (e) {
        document.getElementById("modal-prod-error").textContent = e.message;
    }
});

// ── Kategorie-Modal (statischer Listener) ─────────────────────────────────────

async function oeffneKategorieEditModal(k) {
    if (!await checkPasswort()) return;
    document.getElementById("modal-kat-titel").textContent = "Kategorie bearbeiten";
    document.getElementById("modal-kat-name").value = k.name;
    document.getElementById("modal-kat-error").textContent = "";
    const delBtn = document.getElementById("modal-kat-loeschen");
    delBtn.style.display = "";
    delBtn.textContent = "🗑 Kategorie löschen";
    delete delBtn.dataset.confirm;
    openModal("modal-kategorie");
    setTimeout(() => document.getElementById("modal-kat-name").focus(), 50);
}

document.getElementById("btn-kat-neu").addEventListener("click", async () => {
    if (!await checkPasswort()) return;
    document.getElementById("modal-kat-titel").textContent = "Neue Kategorie";
    document.getElementById("modal-kat-name").value = "";
    document.getElementById("modal-kat-error").textContent = "";
    document.getElementById("modal-kat-loeschen").style.display = "none";
    openModal("modal-kategorie");
    setTimeout(() => document.getElementById("modal-kat-name").focus(), 50);
});

document.getElementById("modal-kat-ok").addEventListener("click", async () => {
    const name = document.getElementById("modal-kat-name").value.trim();
    const err = document.getElementById("modal-kat-error");
    if (!name) return;

    const isEdit = document.getElementById("modal-kat-titel").textContent.includes("bearbeiten");

    try {
        if (isEdit) {
            await api("PUT", `/produkte/kategorien/${state.katId}`, { name });
            showToast(`✓ Kategorie "${name}" aktualisiert.`);
        } else {
            const res = await api("POST", "/produkte/kategorien", { name });
            state.katId = res.id;
            showToast(`✓ Kategorie "${name}" angelegt.`);
        }
        closeModal();
        await ladeKategorienUndProdukte();
    } catch (e) { err.textContent = e.message; }
});

document.getElementById("modal-kat-loeschen").addEventListener("click", async () => {
    const btn = document.getElementById("modal-kat-loeschen");
    const err = document.getElementById("modal-kat-error");

    if (btn.dataset.confirm !== "1") {
        btn.textContent = "⚠ Nochmal antippen zum Löschen";
        btn.dataset.confirm = "1";
        setTimeout(() => {
            if (btn.dataset.confirm === "1") {
                btn.textContent = "🗑 Kategorie löschen";
                delete btn.dataset.confirm;
            }
        }, 3000);
        return;
    }

    try {
        await api("DELETE", `/produkte/kategorien/${state.katId}`);
        state.katId = null;
        closeModal();
        await ladeKategorienUndProdukte();
        showToast("🗑 Kategorie gelöscht.");
    } catch (e) { err.textContent = e.message; }
});

// ── Enter-Taste Helper ────────────────────────────────────────────────────────

document.getElementById("modal-kat-name").addEventListener("keydown", (e) => {
    if (e.key === "Enter") document.getElementById("modal-kat-ok").click();
});

["modal-prod-name", "modal-prod-preis"].forEach(id => {
    document.getElementById(id).addEventListener("keydown", (e) => {
        if (e.key === "Enter") document.getElementById("modal-prod-ok").click();
    });
});

// ── Sortier-Modus Toggler & Helpers ──────────────────────────────────────────
state.sortMode = false;
let draggedElement = null;

const sortToggle = document.getElementById("btn-sort-toggle");
if (sortToggle) {
    sortToggle.addEventListener("click", async () => {
        if (!state.sortMode) {
            // Beim Aktivieren das Passwort abfragen
            if (!await checkPasswort()) return;
            state.sortMode = true;
            sortToggle.textContent = "✓ Fertig";
            sortToggle.classList.add("btn-success");
            document.getElementById("tab-bestellung").classList.add("sort-mode");
        } else {
            state.sortMode = false;
            sortToggle.textContent = "Sortieren ⇄";
            sortToggle.classList.remove("btn-success");
            document.getElementById("tab-bestellung").classList.remove("sort-mode");
        }
        await ladeKategorienUndProdukte();
    });
}

function makeElementSortable(el, onDropCallback) {
    // Desktop Drag & Drop
    el.addEventListener("dragstart", function(e) {
        draggedElement = this;
        e.dataTransfer.effectAllowed = "move";
    });
    
    el.addEventListener("dragover", function(e) {
        e.preventDefault();
        if (draggedElement && draggedElement !== this && draggedElement.parentNode === this.parentNode) {
            const children = Array.from(this.parentNode.children);
            const draggedIdx = children.indexOf(draggedElement);
            const siblingIdx = children.indexOf(this);
            if (draggedIdx < siblingIdx) {
                this.parentNode.insertBefore(draggedElement, this.nextSibling);
            } else {
                this.parentNode.insertBefore(draggedElement, this);
            }
        }
    });
    
    el.addEventListener("drop", function(e) {
        e.preventDefault();
    });
    
    el.addEventListener("dragend", function(e) {
        draggedElement = null;
        onDropCallback();
    });
    
    // Mobile/Tablet Touch Drag & Drop
    el.addEventListener("touchstart", function(e) {
        if (!state.sortMode) return;
        draggedElement = this;
        // Prevent scrolling while dragging
        e.stopPropagation();
    }, { passive: true });
    
    el.addEventListener("touchmove", function(e) {
        if (!state.sortMode || !draggedElement) return;
        
        const touch = e.touches[0];
        const target = document.elementFromPoint(touch.clientX, touch.clientY);
        if (!target) return;
        
        const sibling = target.closest(".kat-tab") || target.closest(".produkt-karte");
        if (sibling && sibling.parentNode === draggedElement.parentNode && draggedElement !== sibling) {
            if (sibling.classList.contains("add-produkt-btn")) return;
            
            const children = Array.from(sibling.parentNode.children);
            const draggedIdx = children.indexOf(draggedElement);
            const siblingIdx = children.indexOf(sibling);
            if (draggedIdx < siblingIdx) {
                sibling.parentNode.insertBefore(draggedElement, sibling.nextSibling);
            } else {
                sibling.parentNode.insertBefore(draggedElement, sibling);
            }
        }
    });
    
    el.addEventListener("touchend", function(e) {
        if (!state.sortMode || !draggedElement) return;
        draggedElement = null;
        onDropCallback();
    });
}

async function speichereKategorienReihenfolge() {
    const ids = Array.from(document.querySelectorAll("#kategorie-tabs .kat-tab")).map(btn => parseInt(btn.dataset.kid)).filter(id => !isNaN(id));
    try {
        await api("POST", "/produkte/kategorien/reorder", { ids });
    } catch (e) {
        showToast(e.message, true);
    }
}

async function speichereProdukteReihenfolge() {
    const ids = Array.from(document.querySelectorAll("#produkt-grid .produkt-karte")).map(card => parseInt(card.dataset.pid)).filter(id => !isNaN(id));
    try {
        await api("POST", "/produkte/reorder", { ids });
        // Add button wieder ans Ende schieben
        const grid = document.getElementById("produkt-grid");
        const addBtn = grid.querySelector(".add-produkt-btn");
        if (addBtn) grid.appendChild(addBtn);
    } catch (e) {
        showToast(e.message, true);
    }
}

// Init
ladeKategorienUndProdukte();
