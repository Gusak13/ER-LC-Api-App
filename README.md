# ER:LC Control Panel

A simple web-based dashboard for managing your [Emergency Response: Liberty County](https://www.roblox.com/games/2534724415/Emergency-Response-Liberty-County) private server. 

Instead of messing with raw API responses, this app gives you a clean UI to track server status, monitor active players, view live player locations on a postal map, and send console commands.

The project runs as a single FastAPI application split into two parts:
* **Python Backend** – Handles all heavy lifting, talks directly to the official ER:LC API, and keeps your private server key secure in memory.
* **Server-Rendered Frontend** – A lightweight, fast web interface that dynamically displays live server metrics and provides interactive admin controls.

## How it works (Data Resources)

* **[ER:LC Private Server API](https://apidocs.erlc.gg/)** – Used as the primary data stream to fetch live player lists, server activity, and to execute remote commands.
* **Postal Map System** – The app takes coordinates provided by the API and maps them onto the local postal map images stored in the `Maps` folder, allowing you to track players visually.

## How to run

### 1. Setup the environment
Open your terminal (preferably PowerShell if on Windows), create a Python virtual environment, install all required dependencies, and initialize your local environment file:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

### 2. Start the server
Run the main script to fire up the FastAPI backend:

```powershell
.\.venv\Scripts\python run.py
```

### 3. Access the dashboard
Once the server is up, open your browser and navigate to `http://127.0.0.1:8000`. You will be prompted to log in using your ER:LC server API key. 

*Note: If you want to access the control panel from other devices (like your phone or a secondary monitor) on the same local network, use `http://<YOUR-PC-IP>:8000`.*

## Security & Configuration

* **API Key Safety:** The server key is strictly held in the server's volatile memory. It never gets saved to the browser cookies, local storage, or any database. 
* **Network Warning:** This tool is built strictly for local host or trusted home network deployment. **Do not** expose this application directly to the public internet without proper reverse proxy authentication (like Nginx with Basic Auth).
* **Command Restricting:** Remote commands are enabled by default. If you want to lock down the dashboard so users can only trigger specific actions, edit the `.env` file and define your limits in the `COMMAND_ALLOWLIST` variable (use a comma-separated list).

## AI disclaimer

Used an AI assistant during development to brainstorm logic, debug code blocks, and speed up boilerplate creation. Every line of generated code was manually reviewed, refactored, and tested to ensure it fits the project.
