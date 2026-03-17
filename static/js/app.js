/* ─── app.js – Gemeinsame Hilfsfunktionen & Tab-Navigation ─── */

// ── API-Wrapper ──────────────────────────────────────────────────────────────

async function api(method, path, body = null) {
    const opts = {
        method,
        headers: { "Content-Type": "application/json" },
    };
    if (body !== null) opts.body = JSON.stringify(body);
    const res = await fetch("/api" + path, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "Serverfehler");
    return data;
}

// ── Toast ────────────────────────────────────────────────────────────────────

let _toastTimer;
function showToast(text, isError = false) {
    const el = document.getElementById("toast");
    clearTimeout(_toastTimer);
    el.textContent = text;
    el.className = "toast show" + (isError ? " error" : "");
    _toastTimer = setTimeout(() => { el.className = "toast"; }, 3000);
}

// ── Tab-Navigation ───────────────────────────────────────────────────────────

document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const key = btn.dataset.tab;
        // Buttons
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b === btn));
        // Inhalte
        document.querySelectorAll(".tab-content").forEach(c => {
            c.classList.toggle("active", c.id === "tab-" + key);
        });
        // Seiteneffekte
        if (key === "dashboard") ladeDashboard();
        if (key === "statistik" && window._statUnlocked) {
            if (typeof refreshStatistik === "function") refreshStatistik();
            else if (typeof ladeStatistik === "function") ladeStatistik();
        }
    });
});

// ── Hilfsfunktionen ──────────────────────────────────────────────────────────

function eur(wert) {
    return wert.toFixed(2).replace(".", ",") + " €";
}

function formatDatum(str) {
    if (!str) return "";
    return str.slice(0, 16).replace("T", " ");
}

// ── Modal ────────────────────────────────────────────────────────────────────

function openModal(id) {
    document.getElementById("modal-backdrop").style.display = "flex";
    document.querySelectorAll(".modal").forEach(m => m.style.display = m.id === id ? "" : "none");
}
function closeModal() {
    document.getElementById("modal-backdrop").style.display = "none";
}

// Schließen bei Klick außerhalb
document.getElementById("modal-backdrop").addEventListener("click", e => {
    if (e.target.id === "modal-backdrop") closeModal();
});

// ── Globaler State ───────────────────────────────────────────────────────────
window.state = {
    person: null,        // { id, vorname, nachname }
    bestellungId: null,  // aktuelle Bestellung-ID
    katId: null,         // aktive Kategorie-ID
};

// ── Global App Lock ──────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    const lockScreen = document.getElementById("global-lock-screen");
    const pinInput = document.getElementById("global-pin-input");
    const unlockBtn = document.getElementById("btn-global-unlock");
    const errorMsg = document.getElementById("global-pin-error");

    if (!lockScreen) return;

    // Prüfen, ob schon entsperrt
    if (localStorage.getItem("appUnlocked") === "true") {
        lockScreen.style.display = "none";
        document.getElementById("sidebar").style.display = "";
        document.querySelector(".main-content").style.display = "";
        return;
    }

    unlockBtn.addEventListener("click", async () => {
        const pin = pinInput.value;
        if (!pin) {
            errorMsg.textContent = "Bitte PIN eingeben.";
            return;
        }

        try {
            await api("POST", "/app/auth", { pin: pin });
            localStorage.setItem("appUnlocked", "true");
            lockScreen.style.display = "none";
            document.getElementById("sidebar").style.display = "";
            document.querySelector(".main-content").style.display = "";
            errorMsg.textContent = "";
        } catch (e) {
            errorMsg.textContent = "❌ Falscher PIN!";
            pinInput.value = "";
            pinInput.focus();
        }
    });

    pinInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            unlockBtn.click();
        }
    });
});
