# ER:LC Control Panel

A simple web dashboard to manage your [Emergency Response: Liberty County](https://roblox.com) private server. 

This app gives you a clean webpage to see who is playing, check where they are on the map, and send server commands easily.

I built this using Python. It works like this:
* It connects to the Roblox server API to get live data.
* It shows everything on a nice webpage with buttons to control the server.
* Your private server key stays safe inside the Python script and never leaks to the browser.

## How it gets data

* **[ER:LC Private Server API](https://erlc.gg)** - Used to get the live player list, player activity, and to send commands.
* **Map Images** - The app takes the X/Y coordinates from the API and draws them onto the game map images stored inside the `Maps` folder.

## How to run

### 1. Setup Python
Open PowerShell (if you are on Windows), create a virtual environment so the packages don't mess up your PC, and copy the config file:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

### 2. Start the app
Run the main Python file to start the web server:

```powershell
.\.venv\Scripts\python run.py
```

### 3. Open it in your browser
Go to `http://127.0.0.1:8000` in your browser. Log in using your ER:LC server API key. 

*Tip: If you want to open this on your phone while playing on your PC, use `http://<YOUR-PC-IP>:8000` (both devices must be on the same Wi-Fi).*

## Security & Settings

* **API Key Safety:** The app only keeps your key in the PC's memory while running. It doesn't save it into cookies or local storage.
* **Don't share it on the internet:** This is made for home use. Don't host it on a public website, otherwise people could steal your server key and ruin your Roblox server.
* **Locking commands:** Anyone who opens the webpage can use the commands by default. If you want to block some commands, open the `.env` file and type the allowed ones into `COMMAND_ALLOWLIST` (like: `kick,ban,m`).

## AI disclaimer

I am still learning, so I used AI to help me understand how things work, debug errors, and help write some parts of the code. I made sure to check everything and adjust it to make it work for this project.
