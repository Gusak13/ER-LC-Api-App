# ER:LC Control Panel

This app is a simple web control panel for an [Emergency Response: Liberty County](https://www.roblox.com/games/2534724415/Emergency-Response-Liberty-County) private server.

It displays the current server status, players, activity and player locations on a map. It can also send allowed commands to the server.

The project is built as one FastAPI app:

* A Python backend communicates with the ER:LC API and keeps the server key private
* A server-rendered web interface displays the data and provides the controls

## Used data resources

The app uses the official [ER:LC Private Server API](https://apidocs.erlc.gg/) to retrieve live server data and send commands.

Player locations are displayed using the local postal map images in the `Maps` folder.

## How to run

Create a virtual environment, install the dependencies and copy the example configuration:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Start the app:

```powershell
.\.venv\Scripts\python run.py
```

Open `http://127.0.0.1:8000` and sign in with your ER:LC server API key. Other devices on the same network can use `http://<YOUR-PC-IP>:8000`.

## Security

The server key is kept in server memory and is not stored in the browser. This app is intended for local or trusted-network use and should not be exposed directly to the internet.

Commands are enabled by default. Set `COMMAND_ALLOWLIST` in `.env` to a comma-separated list if you want to restrict them.

## AI disclaimer

AI was used during the creation of this project to help explain concepts and assist with parts of the code. Generated code was reviewed and adjusted to fit the project.
