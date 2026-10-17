import flet as ft
import flet_webview as fwv

async def main(page: ft.Page):
    wv = fwv.WebView(expand=True)
    page.add(wv)
    page.update()

    # Aspetta che il WebView sia montato
    import asyncio
    await asyncio.sleep(1)

    await wv.set_javascript_mode(ft.JavaScriptMode.UNRESTRICTED)
    await wv.load_html("<html><body><h1>Ciao dal WebView!</h1><script>console.log('JS attivo')</script></body></html>")

ft.run(main)


