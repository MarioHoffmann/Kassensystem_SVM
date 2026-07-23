/* ─── personen.js – Personenverwaltung ─── */

const personDropdown = document.getElementById("person-dropdown");
const personForm = document.getElementById("person-form");
const personActions = document.getElementById("person-actions");
const btnNeu = document.getElementById("btn-person-neu");
const btnAbbrechen = document.getElementById("btn-person-abbrechen");
const btnSpeichern = document.getElementById("btn-person-speichern");
const btnLoeschen = document.getElementById("btn-person-loeschen");
const personStatus = document.getElementById("person-status");

async function ladePersonen() {
    const liste = await api("GET", "/personen/");
    personDropdown.innerHTML = '<option value="">— Person wählen —</option>';
    liste.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = `${p.nachname}, ${p.vorname}`;
        if (state.person && state.person.id === p.id) opt.selected = true;
        personDropdown.appendChild(opt);
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
btnLoeschen.addEventListener("click", () => {
    if (!state.person) return;

    // Passwort-Modal vorbereiten und öffnen
    const pwInput = document.getElementById("modal-pw-input");
    const pwError = document.getElementById("modal-pw-error");
    const pwOk    = document.getElementById("modal-pw-ok");
    const pwAbbruch = document.getElementById("modal-pw-abbruch");

    pwInput.value = "";
    pwError.textContent = "";

    // Modal-Titel anpassen
    document.querySelector("#modal-passwort h3").textContent =
        `🗑️ ${state.person.name} löschen?`;
    document.querySelector("#modal-passwort p").textContent =
        "Achtung: Das komplette Profil wird gelöscht – auch alle offenen Beträge!";

    openModal("modal-passwort");
    setTimeout(() => pwInput.focus(), 100);

    // Einmalige Event-Handler (werden nach Abschluss entfernt)
    async function doLoeschen() {
        const pw = pwInput.value;
        if (!pw) { pwError.textContent = "Bitte Passwort eingeben."; return; }
        try {
            await api("DELETE", "/personen/" + state.person.id, { passwort: pw });
            closeModal();
            state.person = null;
            state.bestellungId = null;
            btnLoeschen.style.display = "none";
            document.getElementById("person-badge").textContent = "";
            await ladePersonen();
            ladeWarenkorb();
            setPersonStatus("Person erfolgreich gelöscht.");
        } catch (e) {
            pwError.textContent = "❌ " + e.message;
            pwInput.value = "";
            pwInput.focus();
        }
    }

    function doAbbruch() {
        closeModal();
        cleanup();
    }

    function onKeydown(e) {
        if (e.key === "Enter") doLoeschen();
    }

    function cleanup() {
        pwOk.removeEventListener("click", doLoeschen);
        pwAbbruch.removeEventListener("click", doAbbruch);
        pwInput.removeEventListener("keydown", onKeydown);
    }

    // Alte Listener entfernen und neue setzen
    pwOk.replaceWith(pwOk.cloneNode(true));
    pwAbbruch.replaceWith(pwAbbruch.cloneNode(true));
    const newOk     = document.getElementById("modal-pw-ok");
    const newAbbruch = document.getElementById("modal-pw-abbruch");
    newOk.addEventListener("click", doLoeschen);
    newAbbruch.addEventListener("click", () => { closeModal(); });
    pwInput.addEventListener("keydown", onKeydown);
});

// Init
ladePersonen();
