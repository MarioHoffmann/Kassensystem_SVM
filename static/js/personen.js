/* ─── personen.js – Personenverwaltung ─── */

const personDropdown = document.getElementById("person-dropdown");
const personForm = document.getElementById("person-form");
const personActions = document.getElementById("person-actions");
const btnNeu = document.getElementById("btn-person-neu");
const btnAbbrechen = document.getElementById("btn-person-abbrechen");
const btnSpeichern = document.getElementById("btn-person-speichern");
const btnLoeschen = document.getElementById("btn-person-loeschen");
const personStatus = document.getElementById("person-status");

let _personenListe = [];

async function ladePersonen() {
    _personenListe = await api("GET", "/personen/");
    renderPersonen();
}

function renderPersonen(filterText = "") {
    const query = filterText.toLowerCase().trim();
    personDropdown.innerHTML = '<option value="">— Person wählen —</option>';
    
    _personenListe.forEach(p => {
        const name = `${p.nachname}, ${p.vorname}`;
        if (query && !name.toLowerCase().includes(query)) return;
        
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = name;
        if (state.person && state.person.id === p.id) opt.selected = true;
        personDropdown.appendChild(opt);
    });
}

// Suchleiste Event-Listener
const personSearch = document.getElementById("person-search");
if (personSearch) {
    personSearch.addEventListener("input", (e) => {
        renderPersonen(e.target.value);
    });
    
    personSearch.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            const options = personDropdown.options;
            if (options.length > 1) {
                personDropdown.value = options[1].value;
                personDropdown.dispatchEvent(new Event("change"));
                personSearch.value = "";
                renderPersonen();
            }
        }
    });
}

function setPersonStatus(msg, isError = false) {
    personStatus.textContent = msg;
    personStatus.className = "status-msg" + (isError ? " error" : "");
    if (msg) setTimeout(() => { personStatus.textContent = ""; }, 3000);
}

// Dropdown-Wahl
personDropdown.addEventListener("change", () => {
    const id = parseInt(personDropdown.value);
    if (!id) {
        state.person = null;
        state.bestellungId = null;
        btnLoeschen.style.display = "none";
        document.getElementById("person-badge").textContent = "";
        ladeWarenkorb();
        return;
    }
    const opt = personDropdown.selectedOptions[0];
    state.person = { id, name: opt.textContent };
    btnLoeschen.style.display = "";
    document.getElementById("person-badge").textContent = opt.textContent;
    ladeBestellung(id);
});

// + Neu
btnNeu.addEventListener("click", () => {
    personForm.style.display = "";
    personActions.style.display = "none";
    document.getElementById("input-vorname").focus();
});

// Abbrechen
btnAbbrechen.addEventListener("click", () => {
    personForm.style.display = "none";
    personActions.style.display = "";
    document.getElementById("input-vorname").value = "";
    document.getElementById("input-nachname").value = "";
});

// Speichern
btnSpeichern.addEventListener("click", async () => {
    const vorname = document.getElementById("input-vorname").value.trim();
    const nachname = document.getElementById("input-nachname").value.trim();
    if (!vorname || !nachname) {
        setPersonStatus("Vorname und Nachname sind Pflichtfelder.", true);
        return;
    }
    try {
        await api("POST", "/personen/", { vorname, nachname });
        document.getElementById("input-vorname").value = "";
        document.getElementById("input-nachname").value = "";
        personForm.style.display = "none";
        personActions.style.display = "";
        await ladePersonen();
        setPersonStatus(`${nachname}, ${vorname} angelegt.`);
    } catch (e) {
        setPersonStatus(e.message, true);
    }
});

// Löschen – Passwort-Modal öffnen
btnLoeschen.addEventListener("click", async () => {
    if (!state.person) return;

    const title = `🗑️ ${state.person.name} löschen?`;
    const description = "Achtung: Das komplette Profil wird gelöscht – auch alle offenen Beträge!";

    const pw = await checkPasswort(title, description);
    if (!pw) return;

    try {
        await api("DELETE", "/personen/" + state.person.id, { passwort: pw });
        state.person = null;
        state.bestellungId = null;
        btnLoeschen.style.display = "none";
        document.getElementById("person-badge").textContent = "";
        await ladePersonen();
        ladeWarenkorb();
        setPersonStatus("Person erfolgreich gelöscht.");
    } catch (e) {
        setPersonStatus("❌ " + e.message, true);
    }
});

// Init
ladePersonen();
