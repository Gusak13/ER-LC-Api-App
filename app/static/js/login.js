"use strict";

const loginForm = document.querySelector("#login-form");
const apiKeyInput = document.querySelector("#api-key");
const loginButton = document.querySelector("#login-button");
const loginResult = document.querySelector("#login-result");

function showLoginResult(message, isError = false) {
    loginResult.textContent = message;
    loginResult.classList.toggle("error", isError);
}

loginForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const apiKey = apiKeyInput.value.trim();
    if (!apiKey) {
        apiKeyInput.focus();
        return;
    }

    loginButton.disabled = true;
    apiKeyInput.disabled = true;
    loginButton.textContent = "Checking...";
    showLoginResult("");

    try {
        const response = await fetch("/api/auth/login", {
            method: "POST",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ api_key: apiKey }),
        });
        const payload = await response.json().catch(() => ({}));
        apiKeyInput.value = "";

        if (!response.ok) {
            throw new Error(
                typeof payload.detail === "string"
                    ? payload.detail
                    : "The API key could not be verified."
            );
        }

        window.location.replace("/");
    } catch (error) {
        apiKeyInput.disabled = false;
        loginButton.disabled = false;
        loginButton.textContent = "Log in";
        showLoginResult(
            error instanceof Error ? error.message : "The API key could not be verified.",
            true
        );
        apiKeyInput.focus();
    }
});

window.addEventListener("pagehide", () => {
    if (apiKeyInput) apiKeyInput.value = "";
});
