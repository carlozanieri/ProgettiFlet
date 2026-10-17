# main.py
import argparse
import uvicorn
import flet as ft
from app import main


def run_desktop():
    ft.run(main, view=ft.AppView.FLET_APP)


def run_web(host, port):
    app = ft.run(main, export_asgi_app=True)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CasaBaldini")
    parser.add_argument("--mode", choices=["desktop", "web"], default="desktop")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7777)
    args = parser.parse_args()

    if args.mode == "web":
        run_web(args.host, args.port)
    else:
        run_desktop()