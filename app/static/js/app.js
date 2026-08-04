"use strict";

const statusElement = document.querySelector("#api-status");
const statusText = document.querySelector("#status-text");
const serverName = document.querySelector("#server-name");
const serverMeta = document.querySelector("#server-meta");
const currentPlayers = document.querySelector("#current-players");
const maxPlayers = document.querySelector("#max-players");
const refreshButton = document.querySelector("#refresh-button");
const commandForm = document.querySelector("#command-form");
const commandInput = document.querySelector("#command-input");
const commandButton = document.querySelector("#command-button");
const commandResult = document.querySelector("#command-result");
const sidebar = document.querySelector("#sidebar");
const sidebarToggle = document.querySelector("#sidebar-toggle");
const sidebarOverlay = document.querySelector("#sidebar-overlay");

function setConnectionStatus(state, text) {
    statusElement.classList.remove("online", "offline");
    if (state) statusElement.classList.add(state);
    statusText.textContent = text;
}

function getErrorMessage(payload, fallback) {
    if (typeof payload?.detail === "string") return payload.detail;
    if (typeof payload?.message === "string") return payload.message;
    return fallback;
}

function setSidebar(open) {
    sidebar.classList.toggle("open", open);
    sidebarToggle.classList.toggle("open", open);
    sidebarOverlay.classList.toggle("visible", open);
    document.body.classList.toggle("sidebar-open", open);

    sidebarToggle.setAttribute("aria-expanded", String(open));
    sidebarToggle.setAttribute(
        "aria-label",
        open ? "Close navigation" : "Open navigation"
    );
}

async function loadServer() {
    refreshButton.disabled = true;
    setConnectionStatus("", "Connecting...");

    try {
        const response = await fetch("/api/server", {
            headers: { Accept: "application/json" },
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(getErrorMessage(payload, "Could not reach the server"));
        }

        serverName.textContent = payload.name;
        currentPlayers.textContent = payload.current_players;
        maxPlayers.textContent = payload.max_players;

        const verification = payload.account_verification || "No verification requirement";
        const balance = payload.team_balance ? "Team balance on" : "Team balance off";
        serverMeta.textContent = `${verification} verification · ${balance}`;
        setConnectionStatus("online", "Connected");
    } catch (error) {
        serverName.textContent = "Server unavailable";
        serverMeta.textContent = error instanceof Error ? error.message : "Could not load server details";
        currentPlayers.textContent = "--";
        maxPlayers.textContent = "--";
        setConnectionStatus("offline", "Unavailable");
    } finally {
        refreshButton.disabled = false;
    }
}

async function submitCommand(event) {
    event.preventDefault();
    const command = commandInput.value.trim();
    if (!command) {
        commandInput.focus();
        return;
    }

    commandButton.disabled = true;
    commandInput.disabled = true;
    commandButton.textContent = "Running...";
    commandResult.className = "command-result";
    commandResult.textContent = "Sending command to the private server...";

    try {
        const response = await fetch("/api/commands", {
            method: "POST",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ command }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(getErrorMessage(payload, "The command could not be sent"));
        }

        commandResult.classList.add("success");
        commandResult.textContent = payload.message || "Command sent successfully.";
        commandInput.value = "";
    } catch (error) {
        commandResult.classList.add("error");
        commandResult.textContent = error instanceof Error ? error.message : "The command could not be sent";
    } finally {
        commandButton.disabled = false;
        commandInput.disabled = false;
        commandButton.textContent = "Run";
        commandInput.focus();
    }
}

refreshButton.addEventListener("click", loadServer);
commandForm.addEventListener("submit", submitCommand);
sidebarToggle.addEventListener("click", () => {
    const isOpen = sidebar.classList.contains("open");
    setSidebar(!isOpen);
});
sidebarOverlay.addEventListener("click", () => {
    setSidebar(false);
});
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        setSidebar(false);
    }
});
loadServer();
