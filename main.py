import argparse

from app.client import ERLCAPIError, ERLCClient


def main() -> int:
    parser = argparse.ArgumentParser(description="ER:LC API smoke test")
    parser.add_argument(
        "--command",
        help="run one ER:LC command, for example ':h Hello'",
    )
    args = parser.parse_args()

    try:
        client = ERLCClient()
        if args.command:
            result = client.run_command(args.command)
            print(f"Command result: {result.get('message', 'Success')}")
            return 0

        server = client.get_server()
    except (ERLCAPIError, ValueError) as error:
        print(f"ER:LC request failed: {error}")
        return 1

    print("API responding: HTTP 200")
    print(f"Server: {server.get('Name', 'unknown')}")
    print(
        f"Players: {server.get('CurrentPlayers', 'unknown')}/"
        f"{server.get('MaxPlayers', 'unknown')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())