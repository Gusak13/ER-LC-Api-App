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
const playersList = document.querySelector("#players-list");
const playersSummary = document.querySelector("#players-summary");
const playersUpdated = document.querySelector("#players-updated");
const playersOnline = document.querySelector("#players-online");
const playersTeams = document.querySelector("#players-teams");
const playersWanted = document.querySelector("#players-wanted");
const playersResults = document.querySelector("#players-results");
const refreshPlayersButton = document.querySelector("#refresh-players-button");
const playerSearch = document.querySelector("#player-search");
const teamFilter = document.querySelector("#team-filter");
const playerSort = document.querySelector("#player-sort");
const clearPlayerFiltersButton = document.querySelector("#clear-player-filters");
const moderationDialog = document.querySelector("#moderation-dialog");
const moderationForm = document.querySelector("#moderation-form");
const moderationTitle = document.querySelector("#moderation-title");
const moderationPlayer = document.querySelector("#moderation-player");
const moderationReason = document.querySelector("#moderation-reason");
const moderationResult = document.querySelector("#moderation-result");
const moderationSubmitButton = document.querySelector("#moderation-submit-button");
const moderationCloseButton = document.querySelector("#moderation-close-button");
const moderationCancelButton = document.querySelector("#moderation-cancel-button");
const commandLogsList = document.querySelector("#command-logs-list");
const commandLogsSummary = document.querySelector("#command-logs-summary");
const refreshCommandLogsButton = document.querySelector("#refresh-command-logs-button");
const activityList = document.querySelector("#activity-list");
const activitySummary = document.querySelector("#activity-summary");
const activitySearch = document.querySelector("#activity-search");
const activityFilter = document.querySelector("#activity-filter");
const refreshActivityButton = document.querySelector("#refresh-activity-button");
const bansList = document.querySelector("#bans-list");
const liveMap = document.querySelector("#live-map");
const mapSummary = document.querySelector("#map-summary");
const mapPlayerList = document.querySelector("#map-player-list");
const refreshMapButton = document.querySelector("#refresh-map-button");
const mapStyle = document.querySelector("#map-style");
const mapCanvas = document.querySelector("#map-canvas");
const mapZoomInButton = document.querySelector("#map-zoom-in");
const mapZoomOutButton = document.querySelector("#map-zoom-out");
const mapResetViewButton = document.querySelector("#map-reset-view");
const dashboardUpdated = document.querySelector("#dashboard-updated");
const dashboardOnline = document.querySelector("#dashboard-online");
const dashboardStaffOnline = document.querySelector("#dashboard-staff-online");
const dashboardQueue = document.querySelector("#dashboard-queue");
const dashboardCalls = document.querySelector("#dashboard-calls");
const dashboardVehicles = document.querySelector("#dashboard-vehicles");
const dashboardWanted = document.querySelector("#dashboard-wanted");
const dashboardTeams = document.querySelector("#dashboard-teams");
const dashboardStaff = document.querySelector("#dashboard-staff");
const dashboardStaffTotal = document.querySelector("#dashboard-staff-total");
const dashboardCallsList = document.querySelector("#dashboard-calls-list");
const dashboardVehiclesList = document.querySelector("#dashboard-vehicles-list");
const dashboardQueueList = document.querySelector("#dashboard-queue-list");
const dashboardWantedList = document.querySelector("#dashboard-wanted-list");
const logoutButton = document.querySelector("#logout-button");
const themePresets = document.querySelectorAll(".theme-preset");
const themePrimary = document.querySelector("#theme-primary");
const themeSecondary = document.querySelector("#theme-secondary");
const resetThemeButton = document.querySelector("#reset-theme");

let selectedModeration = null;
let allPlayers = [];
let allActivity = null;
let mapRefreshInFlight = false;
let mapScale = 1;
let mapOffsetX = 0;
let mapOffsetY = 0;
let mapPanStart = null;
const MAP_IMAGE_SIZE = 3121;
const THEME_STORAGE_KEY = "erlc-theme";
const DEFAULT_THEME = { primary: "#8fb6a6", secondary: "#9f8cff" };

function isHexColor(value) {
    return /^#[0-9a-f]{6}$/i.test(value);
}

function readStoredTheme() {
    try {
        const stored = JSON.parse(window.localStorage.getItem(THEME_STORAGE_KEY));
        if (isHexColor(stored?.primary) && isHexColor(stored?.secondary)) return stored;
    } catch {
        // Ignore unavailable storage or malformed values and use the default theme.
    }
    return DEFAULT_THEME;
}

function applyTheme(theme, persist = false) {
    const primary = isHexColor(theme.primary) ? theme.primary.toLowerCase() : DEFAULT_THEME.primary;
    const secondary = isHexColor(theme.secondary) ? theme.secondary.toLowerCase() : DEFAULT_THEME.secondary;

    document.documentElement.style.setProperty("--primary", primary);
    document.documentElement.style.setProperty("--secondary", secondary);
    if (themePrimary) themePrimary.value = primary;
    if (themeSecondary) themeSecondary.value = secondary;

    themePresets.forEach((preset) => {
        const selected = preset.dataset.primary?.toLowerCase() === primary
            && preset.dataset.secondary?.toLowerCase() === secondary;
        preset.setAttribute("aria-pressed", String(selected));
    });

    if (persist) {
        try {
            window.localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify({ primary, secondary }));
        } catch {
            // The theme still applies for this page when storage is unavailable.
        }
    }
}

applyTheme(readStoredTheme());

function setConnectionStatus(state, text) {
    if (!statusElement || !statusText) return;

    statusElement.classList.remove("online", "offline");
    if (state) statusElement.classList.add(state);
    statusText.textContent = text;
}

function getErrorMessage(payload, fallback) {
    if (typeof payload?.detail === "string") return payload.detail;
    if (typeof payload?.message === "string") return payload.message;
    return fallback;
}

function redirectIfSignedOut(response) {
    if (response.status !== 401) return false;
    window.location.replace("/login?expired=1");
    return true;
}

function setSidebar(open) {
    if (!sidebar || !sidebarToggle || !sidebarOverlay) return;

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

function createDashboardEmpty(message) {
    const empty = document.createElement("p");
    empty.className = "dashboard-empty";
    empty.textContent = message;
    return empty;
}

function createDashboardRow(title, details, tone = "") {
    const row = document.createElement("div");
    row.className = `dashboard-row ${tone}`.trim();
    const copy = document.createElement("div");
    const heading = document.createElement("strong");
    heading.textContent = title;
    const meta = document.createElement("span");
    meta.textContent = details;
    copy.append(heading, meta);
    row.append(copy);
    return row;
}

function setDashboardText(element, value) {
    if (element) element.textContent = String(value);
}

function renderDashboardList(element, items, emptyMessage) {
    if (!element) return;
    element.replaceChildren(...(items.length ? items : [createDashboardEmpty(emptyMessage)]));
}

function renderDashboard(data) {
    if (!dashboardOnline) return;

    setDashboardText(dashboardOnline, data.current_players ?? 0);
    setDashboardText(dashboardStaffOnline, data.staff_online?.length ?? 0);
    setDashboardText(dashboardQueue, data.queue?.length ?? 0);
    setDashboardText(dashboardCalls, data.emergency_calls?.length ?? 0);
    setDashboardText(dashboardVehicles, data.vehicles?.length ?? 0);
    setDashboardText(dashboardWanted, data.wanted_players?.length ?? 0);
    setDashboardText(
        dashboardUpdated,
        `Updated ${new Intl.DateTimeFormat(undefined, { timeStyle: "medium" }).format(new Date())}`
    );

    const teams = Object.entries(data.team_counts || {}).sort(([, left], [, right]) => right - left);
    if (dashboardTeams) {
        const largestTeam = Math.max(1, ...teams.map(([, count]) => count));
        dashboardTeams.replaceChildren(
            ...(teams.length
                ? teams.map(([team, count]) => {
                    const item = document.createElement("div");
                    item.className = "team-breakdown-item";
                    const heading = document.createElement("div");
                    const name = document.createElement("strong");
                    name.textContent = team;
                    const total = document.createElement("span");
                    total.textContent = String(count);
                    heading.append(name, total);
                    const bar = document.createElement("span");
                    bar.className = "team-breakdown-bar";
                    const fill = document.createElement("span");
                    fill.style.width = `${(count / largestTeam) * 100}%`;
                    bar.append(fill);
                    item.append(heading, bar);
                    return item;
                })
                : [createDashboardEmpty("No players are currently online.")])
        );
    }

    const configuredStaff = Object.values(data.staff_counts || {}).reduce(
        (total, count) => total + Number(count || 0),
        0
    );
    setDashboardText(dashboardStaffTotal, `${configuredStaff} configured`);
    renderDashboardList(
        dashboardStaff,
        (data.staff_online || []).map((staff) =>
            createDashboardRow(
                staff.username,
                `${staff.role} · ${staff.team}${staff.callsign ? ` · ${staff.callsign}` : ""}`,
                "staff-row"
            )
        ),
        "No staff members are currently online."
    );
    renderDashboardList(
        dashboardCallsList,
        (data.emergency_calls || []).map((call) =>
            createDashboardRow(
                `#${call.call_number} · ${call.caller}`,
                `${call.team} · ${call.description} · ${call.position} · ${call.player_count} involved`,
                "call-row"
            )
        ),
        "No active emergency calls."
    );
    renderDashboardList(
        dashboardVehiclesList,
        (data.vehicles || []).map((vehicle) =>
            createDashboardRow(
                vehicle.name,
                `${vehicle.owner}${vehicle.plate ? ` · ${vehicle.plate}` : ""}`,
                "vehicle-row"
            )
        ),
        "No spawned vehicles reported."
    );
    renderDashboardList(
        dashboardQueueList,
        (data.queue || []).map((playerId) =>
            createDashboardRow("Waiting player", `Roblox ID ${playerId}`, "queue-row")
        ),
        "Nobody is waiting in the queue."
    );
    renderDashboardList(
        dashboardWantedList,
        (data.wanted_players || []).map((player) =>
            createDashboardRow(
                player.username,
                `${player.team} · ${player.wanted_stars} wanted star${player.wanted_stars === 1 ? "" : "s"}`,
                "wanted-row"
            )
        ),
        "No wanted players online."
    );
}

function renderDashboardError(message) {
    setDashboardText(dashboardUpdated, "Live dashboard unavailable");
    for (const stat of [
        dashboardOnline,
        dashboardStaffOnline,
        dashboardQueue,
        dashboardCalls,
        dashboardVehicles,
        dashboardWanted,
    ]) {
        setDashboardText(stat, "--");
    }
    for (const list of [
        dashboardTeams,
        dashboardStaff,
        dashboardCallsList,
        dashboardVehiclesList,
        dashboardQueueList,
        dashboardWantedList,
    ]) {
        if (list) list.replaceChildren(createDashboardEmpty(message));
    }
}

async function loadServer() {
    if (!refreshButton || !serverName || !serverMeta || !currentPlayers || !maxPlayers) {
        return;
    }

    refreshButton.disabled = true;
    setConnectionStatus("", "Connecting...");

    try {
        const response = await fetch(dashboardOnline ? "/api/server/dashboard" : "/api/server", {
            headers: { Accept: "application/json" },
        });
        if (redirectIfSignedOut(response)) return;
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
        renderDashboard(payload);
        setConnectionStatus("online", "Connected");
    } catch (error) {
        serverName.textContent = "Server unavailable";
        serverMeta.textContent = error instanceof Error ? error.message : "Could not load server details";
        currentPlayers.textContent = "--";
        maxPlayers.textContent = "--";
        renderDashboardError(serverMeta.textContent);
        setConnectionStatus("offline", "Unavailable");
    } finally {
        refreshButton.disabled = false;
    }
}

async function submitCommand(event) {
    event.preventDefault();
    if (!commandInput || !commandButton || !commandResult) return;

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
        if (redirectIfSignedOut(response)) return;
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

function createPlayerDetail(label, value) {
    const detail = document.createElement("span");
    const name = document.createElement("strong");
    name.textContent = `${label}: `;
    detail.append(name, document.createTextNode(value));
    return detail;
}

function formatPlayerLocation(location) {
    if (!location) return null;

    const street = [location.street_name, location.building_number]
        .filter(Boolean)
        .join(" ");
    const parts = [location.postal_code ? `Postal ${location.postal_code}` : null, street]
        .filter(Boolean);
    return parts.length ? parts.join(" · ") : null;
}

function updateTeamFilter() {
    if (!teamFilter) return;

    const selectedTeam = teamFilter.value;
    const teams = [...new Set(allPlayers.map((player) => player.team).filter(Boolean))]
        .sort((left, right) => left.localeCompare(right));
    teamFilter.replaceChildren(new Option("All teams", ""));
    teams.forEach((team) => teamFilter.add(new Option(team, team)));
    if (teams.includes(selectedTeam)) teamFilter.value = selectedTeam;
}

function updatePlayerStats() {
    if (playersOnline) playersOnline.textContent = allPlayers.length;
    if (playersTeams) {
        playersTeams.textContent = new Set(allPlayers.map((player) => player.team)).size;
    }
    if (playersWanted) {
        playersWanted.textContent = allPlayers.filter(
            (player) => Number(player.wanted_stars) > 0
        ).length;
    }
}

function visiblePlayers() {
    const search = playerSearch?.value.trim().toLocaleLowerCase() || "";
    const selectedTeam = teamFilter?.value || "";
    const sort = playerSort?.value || "name";
    const filtered = allPlayers.filter((player) => {
        const location = formatPlayerLocation(player.location) || "";
        const searchable = [
            player.username,
            player.roblox_id,
            player.team,
            player.permission,
            player.callsign,
            location,
        ]
            .filter((value) => value !== null && value !== undefined)
            .join(" ")
            .toLocaleLowerCase();
        return (!selectedTeam || player.team === selectedTeam) && searchable.includes(search);
    });

    return filtered.sort((left, right) => {
        if (sort === "wanted") {
            const wantedDifference = Number(right.wanted_stars) - Number(left.wanted_stars);
            if (wantedDifference) return wantedDifference;
        }
        if (sort === "team") {
            const teamDifference = left.team.localeCompare(right.team);
            if (teamDifference) return teamDifference;
        }
        return left.username.localeCompare(right.username);
    });
}

function renderVisiblePlayers() {
    if (!playersList || !playersResults) return;

    const players = visiblePlayers();
    playersResults.textContent = `Showing ${players.length} of ${allPlayers.length} player${allPlayers.length === 1 ? "" : "s"}.`;
    if (!players.length) {
        showPlayersMessage(
            allPlayers.length ? "No players match the current search and filters." : "No players are currently in this server."
        );
        return;
    }
    playersList.replaceChildren(...players.map(createPlayerCard));
}

function clearPlayerFilters() {
    if (playerSearch) playerSearch.value = "";
    if (teamFilter) teamFilter.value = "";
    if (playerSort) playerSort.value = "name";
    renderVisiblePlayers();
    playerSearch?.focus();
}

function openModerationDialog(action, player) {
    if (
        !moderationDialog ||
        !moderationTitle ||
        !moderationPlayer ||
        !moderationReason ||
        !moderationResult ||
        !moderationSubmitButton
    ) {
        return;
    }

    selectedModeration = { action, player };
    const actionLabel = action === "ban" ? "Ban" : "Kick";
    moderationTitle.textContent = `${actionLabel} ${player.username}`;
    moderationPlayer.textContent = `You are about to ${action} ${player.username} from ${player.team}.`;
    moderationReason.value = "";
    moderationResult.className = "command-result";
    moderationResult.textContent = "";
    moderationSubmitButton.textContent = `Confirm ${actionLabel}`;
    moderationDialog.showModal();
    moderationReason.focus();
}

function createPlayerCard(player) {
    const card = document.createElement("article");
    card.className = "player-card";

    const details = document.createElement("div");
    const nameRow = document.createElement("div");
    nameRow.className = "player-name-row";

    const name = document.createElement("h3");
    name.className = "player-name";
    name.textContent = player.username;
    nameRow.append(name);

    const team = document.createElement("span");
    team.className = "team-badge";
    team.textContent = player.team;
    nameRow.append(team);

    const playerDetails = document.createElement("div");
    playerDetails.className = "player-details";
    playerDetails.append(
        createPlayerDetail("Roblox ID", player.roblox_id?.toString() || "Unavailable"),
        createPlayerDetail("Role", player.permission),
        createPlayerDetail("Callsign", player.callsign || "None"),
        createPlayerDetail("Wanted", player.wanted_stars?.toString() || "0")
    );
    const location = formatPlayerLocation(player.location);
    if (location) playerDetails.append(createPlayerDetail("Location", location));
    details.append(nameRow, playerDetails);

    const actions = document.createElement("div");
    actions.className = "player-actions";
    for (const action of ["kick", "ban"]) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `player-action-button${action === "ban" ? " ban-action" : ""}`;
        button.textContent = action === "ban" ? "Ban" : "Kick";
        button.addEventListener("click", () => openModerationDialog(action, player));
        actions.append(button);
    }

    card.append(details, actions);
    return card;
}

function showPlayersMessage(message, isError = false) {
    if (!playersList) return;

    const emptyState = document.createElement("p");
    emptyState.className = `players-empty${isError ? " error" : ""}`;
    emptyState.textContent = message;
    playersList.replaceChildren(emptyState);
}

async function loadPlayers() {
    if (!playersList || !playersSummary || !refreshPlayersButton) return;

    refreshPlayersButton.disabled = true;
    playersSummary.textContent = "Refreshing live player list...";
    setConnectionStatus("", "Refreshing...");

    try {
        const response = await fetch("/api/players", {
            headers: { Accept: "application/json" },
        });
        if (redirectIfSignedOut(response)) return;
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(getErrorMessage(payload, "Could not load players"));
        }

        allPlayers = Array.isArray(payload.players) ? payload.players : [];
        playersSummary.textContent = `${allPlayers.length} player${allPlayers.length === 1 ? "" : "s"} online`;
        if (playersUpdated) {
            playersUpdated.textContent = `Updated ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
        }
        updateTeamFilter();
        updatePlayerStats();
        renderVisiblePlayers();
        setConnectionStatus("online", "Connected");
    } catch (error) {
        const message = error instanceof Error ? error.message : "Could not load players";
        allPlayers = [];
        playersSummary.textContent = "Player list unavailable";
        if (playersUpdated) playersUpdated.textContent = "Not updated";
        if (playersOnline) playersOnline.textContent = "--";
        if (playersTeams) playersTeams.textContent = "--";
        if (playersWanted) playersWanted.textContent = "--";
        if (playersResults) playersResults.textContent = "";
        showPlayersMessage(message, true);
        setConnectionStatus("offline", "Unavailable");
    } finally {
        refreshPlayersButton.disabled = false;
    }
}

async function submitModeration(event) {
    event.preventDefault();
    if (
        !selectedModeration ||
        !moderationReason ||
        !moderationResult ||
        !moderationSubmitButton
    ) {
        return;
    }

    const { action, player } = selectedModeration;
    const reason = moderationReason.value.trim();
    const command = `:${action} ${player.username}${reason ? ` ${reason}` : ""}`;
    const actionLabel = action === "ban" ? "Ban" : "Kick";

    moderationSubmitButton.disabled = true;
    moderationReason.disabled = true;
    moderationSubmitButton.textContent = `Sending ${actionLabel}...`;
    moderationResult.className = "command-result";
    moderationResult.textContent = `Sending ${command}`;

    try {
        const response = await fetch("/api/commands", {
            method: "POST",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ command }),
        });
        if (redirectIfSignedOut(response)) return;
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(getErrorMessage(payload, `Could not ${action} player`));
        }

        moderationResult.classList.add("success");
        moderationResult.textContent = `${actionLabel} command sent. Refresh the roster shortly to confirm.`;
    } catch (error) {
        moderationResult.classList.add("error");
        moderationResult.textContent = error instanceof Error ? error.message : `Could not ${action} player`;
    } finally {
        moderationSubmitButton.disabled = false;
        moderationReason.disabled = false;
        moderationSubmitButton.textContent = `Confirm ${actionLabel}`;
    }
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    if (Number.isNaN(date.getTime())) return "Time unavailable";
    return date.toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

function createEmptyState(message, isError = false) {
    const emptyState = document.createElement("p");
    emptyState.className = `players-empty${isError ? " error" : ""}`;
    emptyState.textContent = message;
    return emptyState;
}

function activityEntries(data) {
    const entries = [];
    data.join_logs.forEach((entry) => {
        entries.push({
            kind: entry.joined ? "join" : "leave",
            label: entry.joined ? "Joined" : "Left",
            title: `${entry.player} ${entry.joined ? "joined" : "left"} the server`,
            detail: "Join and leave log",
            timestamp: entry.timestamp,
        });
    });
    data.kill_logs.forEach((entry) => {
        entries.push({
            kind: "kill",
            label: "Kill",
            title: `${entry.killer} killed ${entry.killed}`,
            detail: "Kill log",
            timestamp: entry.timestamp,
        });
    });
    data.command_logs.forEach((entry) => {
        const isModeration = /^:(kick|ban)\b/i.test(entry.command);
        entries.push({
            kind: isModeration ? "moderation" : "command",
            label: isModeration ? "Moderation" : "Command",
            title: `${entry.player} ran ${entry.command}`,
            detail: isModeration ? "Kick or ban command" : "Command log",
            timestamp: entry.timestamp,
        });
    });
    data.mod_calls.forEach((entry) => {
        entries.push({
            kind: "call",
            label: "Mod call",
            title: `Moderator call from ${entry.caller}`,
            detail: entry.moderator ? `Handled by ${entry.moderator}` : "Awaiting moderator",
            timestamp: entry.timestamp,
        });
    });
    return entries.sort((left, right) => right.timestamp - left.timestamp);
}

function createActivityRow(entry) {
    const row = document.createElement("article");
    row.className = "activity-row";

    const kind = document.createElement("span");
    kind.className = `activity-kind ${entry.kind}`;
    kind.textContent = entry.label;

    const copy = document.createElement("div");
    copy.className = "activity-copy";
    const title = document.createElement("strong");
    title.textContent = entry.title;
    const detail = document.createElement("span");
    detail.textContent = entry.detail;
    copy.append(title, detail);

    const time = document.createElement("time");
    time.className = "activity-time";
    time.dateTime = new Date(entry.timestamp * 1000).toISOString();
    time.textContent = formatTimestamp(entry.timestamp);

    row.append(kind, copy, time);
    return row;
}

function visibleActivity() {
    if (!allActivity) return [];

    const filter = activityFilter?.value || "all";
    const search = activitySearch?.value.trim().toLocaleLowerCase() || "";
    return activityEntries(allActivity).filter((entry) => {
        const filterMatches =
            filter === "all" ||
            (filter === "join" && ["join", "leave"].includes(entry.kind)) ||
            entry.kind === filter;
        const searchMatches = `${entry.title} ${entry.detail}`
            .toLocaleLowerCase()
            .includes(search);
        return filterMatches && searchMatches;
    });
}

function renderActivity() {
    if (!activityList || !activitySummary || !allActivity) return;

    const entries = visibleActivity();
    activitySummary.textContent = `Showing ${entries.length} activity event${entries.length === 1 ? "" : "s"}.`;
    activityList.replaceChildren(
        ...(entries.length
            ? entries.map(createActivityRow)
            : [createEmptyState("No activity matches the current filters.")])
    );

    if (bansList) {
        bansList.replaceChildren(
            ...(allActivity.bans.length
                ? allActivity.bans.map((ban) => {
                    const row = document.createElement("div");
                    row.className = "ban-row";
                    row.textContent = ban.player;
                    return row;
                })
                : [createEmptyState("There are no current bans in the API response.")])
        );
    }
}

function renderCommandHistory() {
    if (!commandLogsList || !commandLogsSummary || !allActivity) return;

    const entries = activityEntries(allActivity).filter(
        (entry) => ["command", "moderation"].includes(entry.kind)
    );
    commandLogsSummary.textContent = `${entries.length} logged command${entries.length === 1 ? "" : "s"}.`;
    commandLogsList.replaceChildren(
        ...(entries.length
            ? entries.map(createActivityRow)
            : [createEmptyState("No command logs are currently available.")])
    );
}

async function fetchActivity() {
    const response = await fetch("/api/activity", {
        headers: { Accept: "application/json" },
    });
    if (redirectIfSignedOut(response)) return {};
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(getErrorMessage(payload, "Could not load server activity"));
    }
    return payload;
}

async function loadActivityPage() {
    if (!activityList || !activitySummary || !refreshActivityButton) return;

    refreshActivityButton.disabled = true;
    activitySummary.textContent = "Refreshing activity...";
    try {
        allActivity = await fetchActivity();
        renderActivity();
        setConnectionStatus("online", "Connected");
    } catch (error) {
        const message = error instanceof Error ? error.message : "Could not load server activity";
        activitySummary.textContent = "Activity unavailable";
        activityList.replaceChildren(createEmptyState(message, true));
        bansList?.replaceChildren(createEmptyState(message, true));
        setConnectionStatus("offline", "Unavailable");
    } finally {
        refreshActivityButton.disabled = false;
    }
}

async function loadCommandHistory() {
    if (!commandLogsList || !commandLogsSummary || !refreshCommandLogsButton) return;

    refreshCommandLogsButton.disabled = true;
    commandLogsSummary.textContent = "Refreshing command history...";
    try {
        allActivity = await fetchActivity();
        renderCommandHistory();
        setConnectionStatus("online", "Connected");
    } catch (error) {
        const message = error instanceof Error ? error.message : "Could not load command history";
        commandLogsSummary.textContent = "Command history unavailable";
        commandLogsList.replaceChildren(createEmptyState(message, true));
        setConnectionStatus("offline", "Unavailable");
    } finally {
        refreshCommandLogsButton.disabled = false;
    }
}

function mapPosition(value) {
    const position = (value / MAP_IMAGE_SIZE) * 100;
    return Math.min(99.5, Math.max(0.5, position));
}

function setMapStyle(style) {
    if (!mapCanvas || !mapStyle) return;

    const selectedStyle = style === "snow" ? "snow" : "fall";
    mapCanvas.classList.toggle("map-fall", selectedStyle === "fall");
    mapCanvas.classList.toggle("map-snow", selectedStyle === "snow");
    mapStyle.value = selectedStyle;
}

function clampMapOffset() {
    if (!liveMap) return;

    const bounds = liveMap.getBoundingClientRect();
    const maximumX = Math.max(0, (bounds.width * mapScale - bounds.width) / 2);
    const maximumY = Math.max(0, (bounds.height * mapScale - bounds.height) / 2);
    mapOffsetX = Math.min(maximumX, Math.max(-maximumX, mapOffsetX));
    mapOffsetY = Math.min(maximumY, Math.max(-maximumY, mapOffsetY));
}

function applyMapTransform() {
    if (!mapCanvas) return;

    clampMapOffset();
    mapCanvas.style.transform = `translate(${mapOffsetX}px, ${mapOffsetY}px) scale(${mapScale})`;
}

function setMapZoom(nextScale) {
    mapScale = Math.min(2.5, Math.max(1, nextScale));
    applyMapTransform();
}

function resetMapView() {
    mapScale = 1;
    mapOffsetX = 0;
    mapOffsetY = 0;
    applyMapTransform();
}

function markerTeamClass(team) {
    const normalizedTeam = String(team || "").toLowerCase();
    if (normalizedTeam.includes("fire")) return "team-fire";
    if (normalizedTeam.includes("transport") || normalizedTeam.includes("dot")) {
        return "team-dot";
    }
    if (normalizedTeam.includes("police") || normalizedTeam.includes("sheriff")) {
        return "team-police";
    }
    return "team-civilian";
}

function markerTooltip(player) {
    const callsign = player.callsign || "None";
    return `${player.username}\nID: ${player.roblox_id ?? "Unavailable"}\nRole: ${player.permission || "Civilian"}\nTeam: ${player.team || "Civilian"}\nCallsign: ${callsign}`;
}

function getMapSurface() {
    return mapCanvas || liveMap;
}

function renderMap(players) {
    const mapSurface = getMapSurface();
    if (!mapSurface || !mapSummary || !mapPlayerList) return;

    const locatedPlayers = players.filter(
        (player) => Number.isFinite(player.location?.x) && Number.isFinite(player.location?.z)
    );
    if (!locatedPlayers.length) {
        mapSummary.textContent = "No live player coordinates are available.";
        mapSurface.replaceChildren(createEmptyState("No positioned players are currently available."));
        mapPlayerList.replaceChildren();
        return;
    }

    const markers = locatedPlayers.map((player) => {
        const marker = document.createElement("button");
        marker.type = "button";
        marker.className = `map-marker ${markerTeamClass(player.team)}`;
        marker.style.left = `${mapPosition(player.location.x)}%`;
        marker.style.top = `${mapPosition(player.location.z)}%`;
        const location = formatPlayerLocation(player.location) || "Location unavailable";
        marker.dataset.tooltip = markerTooltip(player);
        marker.title = `${player.username} — ${location}`;
        marker.setAttribute("aria-label", `${markerTooltip(player)}. ${location}`);
        return marker;
    });
    mapSurface.replaceChildren(...markers);

    mapPlayerList.replaceChildren(
        ...locatedPlayers.map((player) => {
            const item = document.createElement("div");
            item.className = "map-player-item";
            const name = document.createElement("strong");
            name.textContent = player.username;
            const location = document.createElement("span");
            location.textContent = formatPlayerLocation(player.location) || "Location unavailable";
            const coordinates = document.createElement("span");
            coordinates.textContent = `X ${player.location.x.toFixed(0)} · Z ${player.location.z.toFixed(0)}`;
            item.append(name, location, coordinates);
            return item;
        })
    );
    mapSummary.textContent = `${locatedPlayers.length} positioned player${locatedPlayers.length === 1 ? "" : "s"}; fixed map coordinates, live updates every 2 seconds.`;
}

async function loadMap() {
    const mapSurface = getMapSurface();
    if (!mapSurface || !mapSummary || !mapPlayerList || !refreshMapButton || mapRefreshInFlight) {
        return;
    }

    mapRefreshInFlight = true;
    refreshMapButton.disabled = true;
    mapSummary.textContent = "Refreshing player locations...";
    try {
        const response = await fetch("/api/players", {
            headers: { Accept: "application/json" },
        });
        if (redirectIfSignedOut(response)) return;
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(getErrorMessage(payload, "Could not load player locations"));
        }
        renderMap(Array.isArray(payload.players) ? payload.players : []);
        setConnectionStatus("online", "Connected");
    } catch (error) {
        const message = error instanceof Error ? error.message : "Could not load player locations";
        mapSummary.textContent = "Map unavailable";
        mapSurface.replaceChildren(createEmptyState(message, true));
        mapPlayerList.replaceChildren();
        setConnectionStatus("offline", "Unavailable");
    } finally {
        mapRefreshInFlight = false;
        refreshMapButton.disabled = false;
    }
}

function beginMapPan(event) {
    if (!liveMap || event.button !== 0 || event.target.closest(".map-marker")) return;

    mapPanStart = {
        pointerId: event.pointerId,
        x: event.clientX,
        y: event.clientY,
        offsetX: mapOffsetX,
        offsetY: mapOffsetY,
    };
    liveMap.setPointerCapture(event.pointerId);
    liveMap.classList.add("is-panning");
}

function moveMapPan(event) {
    if (!mapPanStart || event.pointerId !== mapPanStart.pointerId) return;

    mapOffsetX = mapPanStart.offsetX + event.clientX - mapPanStart.x;
    mapOffsetY = mapPanStart.offsetY + event.clientY - mapPanStart.y;
    applyMapTransform();
}

function endMapPan(event) {
    if (!liveMap || !mapPanStart || event.pointerId !== mapPanStart.pointerId) return;

    if (liveMap.hasPointerCapture(event.pointerId)) {
        liveMap.releasePointerCapture(event.pointerId);
    }
    mapPanStart = null;
    liveMap.classList.remove("is-panning");
}

function initializeMapNavigation() {
    if (!liveMap || !mapCanvas) return;

    mapZoomInButton?.addEventListener("click", () => setMapZoom(mapScale + 0.25));
    mapZoomOutButton?.addEventListener("click", () => setMapZoom(mapScale - 0.25));
    mapResetViewButton?.addEventListener("click", resetMapView);
    liveMap.addEventListener("pointerdown", beginMapPan);
    liveMap.addEventListener("pointermove", moveMapPan);
    liveMap.addEventListener("pointerup", endMapPan);
    liveMap.addEventListener("pointercancel", endMapPan);
    liveMap.addEventListener(
        "wheel",
        (event) => {
            event.preventDefault();
            setMapZoom(mapScale + (event.deltaY < 0 ? 0.15 : -0.15));
        },
        { passive: false }
    );
}

if (commandForm) {
    commandForm.addEventListener("submit", submitCommand);
    if (refreshButton) {
        refreshButton.addEventListener("click", loadServer);
        loadServer();
    }
}

if (sidebar && sidebarToggle && sidebarOverlay) {
    sidebarToggle.addEventListener("click", () => {
        setSidebar(!sidebar.classList.contains("open"));
    });
    sidebarOverlay.addEventListener("click", () => setSidebar(false));
}

logoutButton?.addEventListener("click", async () => {
    logoutButton.disabled = true;
    try {
        await fetch("/api/auth/logout", {
            method: "POST",
            headers: { Accept: "application/json" },
        });
    } finally {
        window.location.replace("/login");
    }
});

if (playersList && refreshPlayersButton && moderationForm) {
    refreshPlayersButton.addEventListener("click", loadPlayers);
    playerSearch?.addEventListener("input", renderVisiblePlayers);
    teamFilter?.addEventListener("change", renderVisiblePlayers);
    playerSort?.addEventListener("change", renderVisiblePlayers);
    clearPlayerFiltersButton?.addEventListener("click", clearPlayerFilters);
    moderationForm.addEventListener("submit", submitModeration);
    moderationCloseButton?.addEventListener("click", () => moderationDialog?.close());
    moderationCancelButton?.addEventListener("click", () => moderationDialog?.close());
    loadPlayers();
}

if (commandLogsList && refreshCommandLogsButton) {
    refreshCommandLogsButton.addEventListener("click", loadCommandHistory);
    loadCommandHistory();
}

if (activityList && refreshActivityButton) {
    refreshActivityButton.addEventListener("click", loadActivityPage);
    activitySearch?.addEventListener("input", renderActivity);
    activityFilter?.addEventListener("change", renderActivity);
    loadActivityPage();
}

if (liveMap && refreshMapButton) {
    refreshMapButton.addEventListener("click", loadMap);
    mapStyle?.addEventListener("change", () => setMapStyle(mapStyle.value));
    setMapStyle(mapStyle?.value);
    initializeMapNavigation();
    loadMap();
    window.setInterval(() => {
        if (!document.hidden) loadMap();
    }, 2000);
}

if (themePrimary && themeSecondary) {
    themePresets.forEach((preset) => {
        preset.addEventListener("click", () => {
            applyTheme(
                { primary: preset.dataset.primary, secondary: preset.dataset.secondary },
                true
            );
        });
    });
    themePrimary.addEventListener("input", () => {
        applyTheme({ primary: themePrimary.value, secondary: themeSecondary.value }, true);
    });
    themeSecondary.addEventListener("input", () => {
        applyTheme({ primary: themePrimary.value, secondary: themeSecondary.value }, true);
    });
    resetThemeButton?.addEventListener("click", () => applyTheme(DEFAULT_THEME, true));
    setConnectionStatus("", "Appearance");
}

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setSidebar(false);
});
