"use strict";

(() => {
    const STORAGE_KEY = "erlc-theme";
    const DEFAULT_THEME = Object.freeze({
        primary: "#8fb6a6",
        secondary: "#9f8cff",
    });
    const DEFAULT_SURFACES = Object.freeze({
        background: "#111513",
        card: "#171c19",
        cardLight: "#1d2420",
        input: "#121714",
        border: "#303a35",
    });

    function isHexColor(value) {
        return typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value);
    }

    function normalizeTheme(theme) {
        if (!isHexColor(theme?.primary) || !isHexColor(theme?.secondary)) return null;
        return {
            primary: theme.primary.toLowerCase(),
            secondary: theme.secondary.toLowerCase(),
        };
    }

    function mixChannel(channel, target, amount) {
        return Math.round(channel + (target - channel) * amount);
    }

    function mixColors(base, tint, amount) {
        const baseChannels = [1, 3, 5].map((start) =>
            Number.parseInt(base.slice(start, start + 2), 16)
        );
        const tintChannels = [1, 3, 5].map((start) =>
            Number.parseInt(tint.slice(start, start + 2), 16)
        );
        const channels = baseChannels.map((channel, index) =>
            mixChannel(channel, tintChannels[index], amount).toString(16).padStart(2, "0")
        );
        return `#${channels.join("")}`;
    }

    function getHoverColor(color) {
        const normalized = isHexColor(color) ? color : DEFAULT_THEME.primary;
        const red = Number.parseInt(normalized.slice(1, 3), 16);
        const green = Number.parseInt(normalized.slice(3, 5), 16);
        const blue = Number.parseInt(normalized.slice(5, 7), 16);
        const brightness = (red * 299 + green * 587 + blue * 114) / 1000;
        const target = brightness > 160 ? 0 : 255;
        const amount = brightness > 160 ? 0.12 : 0.16;
        const channels = [red, green, blue].map((channel) =>
            mixChannel(channel, target, amount).toString(16).padStart(2, "0")
        );
        return `#${channels.join("")}`;
    }

    function getContrastColor(color) {
        const normalized = isHexColor(color) ? color : DEFAULT_THEME.primary;
        const red = Number.parseInt(normalized.slice(1, 3), 16);
        const green = Number.parseInt(normalized.slice(3, 5), 16);
        const blue = Number.parseInt(normalized.slice(5, 7), 16);
        const brightness = (red * 299 + green * 587 + blue * 114) / 1000;
        return brightness >= 150 ? "#101512" : "#ffffff";
    }

    function getThemeSurfaces(theme) {
        const isDefault = theme.primary === DEFAULT_THEME.primary
            && theme.secondary === DEFAULT_THEME.secondary;
        if (isDefault) return DEFAULT_SURFACES;

        return {
            background: mixColors("#0d100f", theme.primary, 0.18),
            card: mixColors("#151817", theme.primary, 0.18),
            cardLight: mixColors("#1b201d", theme.secondary, 0.16),
            input: mixColors("#0f1311", theme.primary, 0.12),
            border: mixColors("#303a35", theme.secondary, 0.28),
        };
    }

    function setThemeProperties(theme) {
        const normalized = normalizeTheme(theme) || DEFAULT_THEME;
        const surfaces = getThemeSurfaces(normalized);
        const root = document.documentElement;
        root.style.setProperty("--background", surfaces.background);
        root.style.setProperty("--card", surfaces.card);
        root.style.setProperty("--card-light", surfaces.cardLight);
        root.style.setProperty("--input", surfaces.input);
        root.style.setProperty("--border", surfaces.border);
        root.style.setProperty("--primary", normalized.primary);
        root.style.setProperty("--secondary", normalized.secondary);
        root.style.setProperty("--accent", normalized.primary);
        root.style.setProperty("--accent-hover", getHoverColor(normalized.primary));
        root.style.setProperty("--accent-contrast", getContrastColor(normalized.primary));
        return normalized;
    }

    function loadStoredTheme() {
        try {
            const stored = normalizeTheme(JSON.parse(window.localStorage.getItem(STORAGE_KEY)));
            if (stored) return stored;
            window.localStorage.removeItem(STORAGE_KEY);
        } catch {
            try {
                window.localStorage.removeItem(STORAGE_KEY);
            } catch {
                // Storage can be unavailable; the default theme still works.
            }
        }
        return DEFAULT_THEME;
    }

    window.ERLCTheme = Object.freeze({
        STORAGE_KEY,
        DEFAULT_THEME,
        DEFAULT_SURFACES,
        getContrastColor,
        getHoverColor,
        getThemeSurfaces,
        isHexColor,
        loadStoredTheme,
        normalizeTheme,
        setThemeProperties,
    });

    setThemeProperties(loadStoredTheme());
})();
