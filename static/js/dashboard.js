/* ─── dashboard.js – Offene Beträge ─── */

let _aktiverGast = null;

async function ladeDashboard() {
  const liste = await api("GET", "/dashboard/");
  const el = document.getElementById("dashboard-liste");
  el.innerHTML = "";

  if (liste.length === 0) {
    el.innerHTML = '<p class="empty-hint" style="color:var(--green)">✓ Keine offenen Beträge.</p>';
    return;
  }

  liste.forEach(g => {
    const card = document.createElement("div");
    card.className = "gast-karte" + ((_aktiverGast && _aktiverGast.id === g.id) ? " selected" : "");
    card.innerHTML = `
      <span class="gast-name">${g.nachname}, ${g.vorname}</span>
      <span class="gast-betrag">${eur(g.offener_betrag)}</span>
    `;
    card.addEventListener("click", () => waehleGast(g, card));
    el.appendChild(card);
  });

  // Wenn noch ein Gast aktiv war, Detail aktualisieren
  if (_aktiverGast) {
    const aktuell = liste.find(g => g.id === _aktiverGast.id);
    if (aktuell) ladeGastDetail(aktuell);
    else resetDetail();
  }
}

async function waehleGast(gast, cardEl) {
  _aktiverGast = gast;
  document.querySelectorAll(".gast-karte").forEach(c => c.classList.remove("selected"));
  cardEl.classList.add("selected");
  ladeGastDetail(gast);
}

async function ladeGastDetail(gast) {
  const detail = document.getElementById("dashboard-detail");
  const data = await api("GET", `/dashboard/${gast.id}`);

  detail.innerHTML = `
    <div class="detail-person-name">${gast.nachname}, ${gast.vorname}</div>
    <div id="bestellungen-liste"></div>
    <div class="detail-footer">
      <div class="gesamt-detail-row">
        <span>Offener Betrag</span>
        <span class="gesamt-detail-wert">${eur(data.gesamt)}</span>
      </div>
      <button class="btn btn-success btn-full" id="btn-bezahlen">💳 Bezahlt</button>
    </div>
  `;

  const bListe = detail.querySelector("#bestellungen-liste");
  data.bestellungen.forEach((b, i) => {
    const block = document.createElement("div");
    block.className = "bestellung-block";
    block.innerHTML = `
      <div class="bestellung-label">
        Bestellung ${i + 1}${data.bestellungen.length > 1 ? ` von ${data.bestellungen.length}` : ""}
        &nbsp;·&nbsp; ${formatDatum(b.erstellt_am)}
      </div>
      <table class="position-table">
        <thead>
          <tr><th>Produkt</th><th>Menge</th><th>Einzel</th><th>Gesamt</th></tr>
        </thead>
        <tbody>
          ${b.positionen.map(p => `
            <tr>
              <td>${p.produkt_name}</td>
              <td class="col-menge">${p.menge}×</td>
              <td>${eur(p.einzelpreis)}</td>
              <td>${eur(p.gesamtpreis)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
      <div class="zwischensumme">Summe: ${eur(b.summe)}</div>
    `;
    bListe.appendChild(block);
  });

  detail.querySelector("#btn-bezahlen").addEventListener("click", async () => {
    if (!await checkPasswort()) return;
    try {
      await api("POST", `/dashboard/${gast.id}/bezahlen`);
      showToast(`✓ ${gast.nachname}, ${gast.vorname} – Bezahlt!`);
      _aktiverGast = null;
      resetDetail();
      ladeDashboard();
      // Optional: Statistik im Hintergrund aktualisieren, falls der Tab gewechselt wird
      if (typeof refreshStatistik === "function") refreshStatistik();
    } catch (e) { showToast(e.message, true); }
  });
}

function resetDetail() {
  document.getElementById("dashboard-detail").innerHTML = `
    <div class="detail-placeholder">
      <span class="big-icon">👤</span>
      <p>Person links auswählen</p>
    </div>
  `;
}

// Polling alle 10 Sekunden wenn Dashboard aktiv
setInterval(() => {
  const dashTab = document.getElementById("tab-dashboard");
  if (dashTab.classList.contains("active")) ladeDashboard();
}, 10000);
