/* ─── statistik.js – Statistik-Dashboard ─── */

window._statUnlocked = false;
let _statModus = "tag";

// ── Passwort-Entsperren ───────────────────────────────────────────────────────

document.getElementById("btn-stat-unlock").addEventListener("click", async () => {
    const pw = document.getElementById("statistik-pw").value;
    try {
        await api("POST", "/statistik/auth", { passwort: pw });
        window._statUnlocked = true;
        document.getElementById("statistik-lock").style.display = "none";
        document.getElementById("statistik-dashboard").style.display = "";
        ladeStatistik();
        ladePersonenDropdownStat();
    } catch (e) {
        document.getElementById("stat-pw-error").textContent = "Falsches Passwort.";
        document.getElementById("statistik-pw").value = "";
    }
});

document.getElementById("statistik-pw").addEventListener("keydown", e => {
    if (e.key === "Enter") document.getElementById("btn-stat-unlock").click();
});

// ── Daten laden ───────────────────────────────────────────────────────────────

async function ladeStatistik() {
    if (!window._statUnlocked) return;
    const data = await api("GET", `/statistik/?modus=${_statModus}`);

    // KPIs
    document.getElementById("kpi-heute").textContent = eur(data.heute.umsatz_heute);
    document.getElementById("kpi-woche").textContent = eur(data.woche.umsatz_woche);
    document.getElementById("kpi-monat").textContent = eur(data.monat.umsatz_monat);

    // Diagramm
    zeichneDiagramm(data.labels, data.werte);

    // Top-Produkte
    const container = document.getElementById("top-produkte-table");
    if (data.top.length === 0) {
        container.innerHTML = '<p class="empty-hint">Noch keine Daten.</p>';
        return;
    }
    container.innerHTML = `
    <table class="top-table">
      <thead>
        <tr><th>#</th><th>Produkt</th><th>Menge</th><th>Umsatz</th></tr>
      </thead>
      <tbody>
        ${data.top.map((p, i) => `
          <tr>
            <td class="top-rank">${i + 1}</td>
            <td>${p.name}</td>
            <td class="top-menge">${p.menge}×</td>
            <td>${eur(p.umsatz)}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

// ── Modus-Buttons ─────────────────────────────────────────────────────────────

function setModus(modus) {
    _statModus = modus;
    document.querySelectorAll(".modus-btns .btn").forEach(b => {
        b.classList.toggle("active", b.dataset.modus === modus);
    });
    refreshStatistik();
}

/**
 * Aktualisiert alle Daten der Statistik-Seite (KPIs, Charts, Top-Produkte UND Kaufhistorie)
 */
function refreshStatistik(silent = false) {
    ladeStatistik();
    ladePersonenDropdownStat(); // Personenliste aktuell halten
    ladePersonenStatistik();
    if (!silent) showToast("Statistik aktualisiert");
}

// ── Canvas-Balkendiagramm ─────────────────────────────────────────────────────

function zeichneDiagramm(labels, werte) {
    const canvas = document.getElementById("umsatz-chart");
    const ctx = canvas.getContext("2d");

    // HiDPI
    const dpr = window.devicePixelRatio || 1;
    const W = canvas.offsetWidth;
    const H = canvas.offsetHeight;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, W, H);

    // Farben aus CSS-Variablen
    const accent = "#cba6f7";
    const subtext = "#a6adc8";
    const border = "#585b70";
    const bg = "#1e1e2e";

    const padL = 52, padR = 12, padT = 16, padB = 32;
    const chartW = W - padL - padR;
    const chartH = H - padT - padB;

    if (!werte || werte.length === 0) {
        ctx.fillStyle = subtext;
        ctx.font = "13px Inter, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("Noch keine Daten für diesen Zeitraum.", W / 2, H / 2);
        return;
    }

    const maxVal = Math.max(...werte, 1);
    const n = werte.length;
    const barW = Math.max(4, (chartW / n) - 4);

    // Gitternetz + Y-Achse
    ctx.strokeStyle = border;
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 6]);
    for (let i = 0; i <= 4; i++) {
        const y = padT + chartH - (chartH * i / 4);
        const label = ((maxVal * i / 4)).toFixed(0);
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(W - padR, y);
        ctx.stroke();
        ctx.fillStyle = subtext;
        ctx.font = "10px Inter, sans-serif";
        ctx.textAlign = "right";
        ctx.fillText(label, padL - 6, y + 4);
    }
    ctx.setLineDash([]);

    // Balken
    for (let i = 0; i < n; i++) {
        const x = padL + i * (chartW / n) + ((chartW / n) - barW) / 2;
        const bH = (werte[i] / maxVal) * chartH;
        const y = padT + chartH - bH;

        // Balken
        ctx.fillStyle = accent;
        const r = Math.min(4, barW / 2);
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + barW - r, y);
        ctx.quadraticCurveTo(x + barW, y, x + barW, y + r);
        ctx.lineTo(x + barW, padT + chartH);
        ctx.lineTo(x, padT + chartH);
        ctx.lineTo(x, y + r);
        ctx.quadraticCurveTo(x, y, x + r, y);
        ctx.fill();

        // Wert im Balken
        if (bH > 20) {
            ctx.fillStyle = bg;
            ctx.font = "bold 10px Inter, sans-serif";
            ctx.textAlign = "center";
            ctx.fillText(werte[i].toFixed(0), x + barW / 2, y + 13);
        }

        // X-Label
        if (n <= 14 || i % 2 === 0) {
            ctx.fillStyle = subtext;
            ctx.font = "10px Inter, sans-serif";
            ctx.textAlign = "center";
            ctx.fillText(labels[i] ? labels[i].slice(-5) : "", x + barW / 2, H - 6);
        }
    }
}

// Neu zeichnen bei Fenstergröße
window.addEventListener("resize", () => {
    if (window._statUnlocked) ladeStatistik();
});

// ── Personen-Kaufhistorie ─────────────────────────────────────────────────────

async function ladePersonenDropdownStat() {
    try {
        const sel = document.getElementById("person-stat-dropdown");
        if (!sel) return;
        const currentVal = sel.value; // Auswahl merken

        const personen = await api("GET", "/personen/");
        while (sel.options.length > 1) sel.remove(1);

        personen
            .sort((a, b) => a.nachname.localeCompare(b.nachname) || a.vorname.localeCompare(b.vorname))
            .forEach(p => {
                const opt = document.createElement("option");
                opt.value = p.id;
                opt.textContent = `${p.nachname}, ${p.vorname}`;
                sel.appendChild(opt);
            });

        if (currentVal) sel.value = currentVal; // Auswahl wiederherstellen
    } catch (e) {
        console.error("Fehler beim Laden der Personen:", e);
    }
}

async function ladePersonenStatistik() {
    const sel = document.getElementById("person-stat-dropdown");
    const container = document.getElementById("personen-kaufhistorie-table");
    const personId = sel.value;

    if (!personId) {
        container.innerHTML = '<p class="empty-hint">Person oben auswählen.</p>';
        return;
    }

    container.innerHTML = '<p class="empty-hint">Lade…</p>';

    let daten;
    try {
        daten = await api("GET", `/statistik/person/${personId}`);
    } catch (e) {
        console.error("Fehler Kaufhistorie:", e);
        container.innerHTML = `<p class="empty-hint" style="color:var(--red)">⚠️ Fehler: ${e.message}</p>`;
        return;
    }

    if (!daten || daten.length === 0) {
        container.innerHTML = '<p class="empty-hint">Keine abgeschlossenen Käufe gefunden.</p>';
        return;
    }

    const summeGesamtRaw = daten.reduce((s, b) => s + b.gesamt, 0);

    // Header mit Gesamtsumme und "Alles Löschen" Button
    let html = `
    <div class="kpi-card" style="margin-bottom:20px; background:var(--bg-lighter); border:1px solid var(--accent)">
        <span class="kpi-label" style="color:var(--accent)">Gesamtausgaben (alle Käufe)</span>
        <span class="kpi-value" style="font-size:24px">${eur(summeGesamtRaw)}</span>
    </div>

    <div class="pin-row" style="margin-bottom:16px; justify-content: flex-end;">
        <button class="btn btn-sm btn-danger" onclick="kaufhistorieLoeschen(${personId})">
            🗑️ Gesamte Historie löschen
        </button>
    </div>`;

    html += daten.map((bestellung) => {
        const datum = bestellung.datum
            ? bestellung.datum.replace("T", " ").substring(0, 16)
            : "–";
        const zeilen = bestellung.positionen.map(p => `
            <tr>
                <td style="padding-left:20px;color:var(--subtext)">${p.produkt}</td>
                <td style="text-align:center">${p.menge}×</td>
                <td style="text-align:right">${eur(p.einzelpreis)}</td>
                <td style="text-align:right">${eur(p.summe)}</td>
            </tr>`).join("");

        // Find ID from the first item if possible (actually we should include it in the model)
        // For now, let's assume we need to update the model to return the ID.
        // Wait, I didn't include the ID in the result of kaeufe_pro_person. Fix that first.
        return `
        <table class="top-table" style="margin-bottom:20px">
            <thead>
                <tr>
                    <th colspan="2">📅 ${datum}</th>
                    <th style="text-align:right;color:var(--green)">∑ ${eur(bestellung.gesamt)}</th>
                    <th style="text-align:right;width:100px">
                         <button class="btn btn-sm btn-danger" style="min-height:30px;padding:0 8px" 
                                 onclick="bestellungLoeschen(${bestellung.id})">Löschen</button>
                    </th>
                </tr>
            </thead>
            <tbody>
                ${zeilen}
            </tbody>
        </table>`;
    }).join("");

    container.innerHTML = html;
}

async function kaufhistorieLoeschen(personId) {
    if (!confirm("Möchtest du wirklich die GESAMTE Kaufhistorie dieser Person unwiderruflich löschen?")) return;

    try {
        await api("DELETE", `/statistik/person/${personId}/historie`);
        showToast("Historie gelöscht");
        refreshStatistik(); // Alles aktualisieren
    } catch (e) {
        showToast("Fehler: " + e.message, true);
    }
}

async function bestellungLoeschen(bestellungId) {
    if (!confirm("Diese Bestellung wirklich löschen?")) return;

    try {
        await api("DELETE", `/statistik/bestellung/${bestellungId}`);
        showToast("Bestellung gelöscht");
        refreshStatistik(); // Alles aktualisieren
    } catch (e) {
        showToast("Fehler: " + e.message, true);
    }
}
