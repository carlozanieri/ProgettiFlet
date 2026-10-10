# app/views/auth.py
import flet as ft
from api_client import APIClient
import asyncio

# ============================================================
# VISTA DI LOGIN
# ============================================================

def build_login_view(
    page: ft.Page,
    api: APIClient,
    prefs,
    on_success,
    on_register_click,
    on_back,
) -> ft.Container:
    """
    Costruisce la vista di login.
    
    on_success: callback(user_data) chiamata dopo login riuscito
    on_register_click: callback() per andare alla registrazione
    on_back: callback() per tornare alla vista precedente
    """
    error_text = ft.Text("", color=ft.Colors.RED_700, size=13, visible=False)
    loading = ft.ProgressRing(width=20, height=20, visible=False)

    username_field = ft.TextField(
        label="Username",
        width=320,
        autofocus=True,
        text_size=16,
        content_padding=15,
    )

    password_field = ft.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        width=320,
        text_size=16,
        content_padding=15,
    )

    async def do_login(e):
        error_text.visible = False
        loading.visible = True
        page.update()

        username = username_field.value.strip()
        password = password_field.value

        if not username or not password:
            error_text.value = "Inserisci username e password."
            error_text.visible = True
            loading.visible = False
            page.update()
            return

        success, data = api.login(username, password)
        loading.visible = False

        if success:
            await prefs.set("auth_token", data["access_token"])
            await prefs.set("user_id", data["user_id"])
            await prefs.set("username", data["username"])
            on_success(data)
        else:
            error_text.value = data
            error_text.visible = True
            page.update()

    login_button = ft.Button(
        content=ft.Text("Accedi", size=16, weight=ft.FontWeight.BOLD),
        width=320,
        height=50,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BROWN_700,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=do_login,
    )

    password_field.on_submit = do_login

    register_link = ft.TextButton(
        content=ft.Text("Non hai un account? Registrati", size=14),
        on_click=lambda e: on_register_click(),
    )

    back_link = ft.TextButton(
        content=ft.Text("← Torna indietro", size=14),
        on_click=lambda e: on_back(),
    )

    card = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.PERSON_OUTLINE, size=60, color=ft.Colors.BROWN_700),
            ft.Text("Accedi a InCantoPipe", size=24, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BROWN_700),
            ft.Text("Inserisci le tue credenziali", size=13,
                    color=ft.Colors.GREY_600),
            ft.Container(height=20),
            username_field,
            ft.Container(height=10),
            password_field,
            ft.Container(height=5),
            error_text,
            ft.Container(height=10),
            ft.Row([loading], alignment=ft.MainAxisAlignment.CENTER),
            login_button,
            ft.Container(height=10),
            register_link,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=5),
        padding=30,
        bgcolor=ft.Colors.WHITE,
        border_radius=12,
        shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.GREY_300),
    )

    return ft.Container(
        content=ft.Column([
            back_link,
            ft.Container(height=20),
            ft.Row([card], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=0),
        padding=20,
        alignment=ft.Alignment.TOP_CENTER,
    )


# ============================================================
# VISTA DI REGISTRAZIONE
# ============================================================

def build_register_view(
    page: ft.Page,
    api: APIClient,
    prefs,
    on_success,
    on_login_click,
    on_back,
) -> ft.Container:
    """
    Costruisce la vista di registrazione.
    
    on_success: callback(user_data) dopo registrazione + login automatico
    on_login_click: callback() per andare al login
    on_back: callback() per tornare alla vista precedente
    """
    error_text = ft.Text("", color=ft.Colors.RED_700, size=13, visible=False)
    loading = ft.ProgressRing(width=20, height=20, visible=False)

    first_name_field = ft.TextField(
        label="Nome", width=320, text_size=16, content_padding=15,
    )
    last_name_field = ft.TextField(
        label="Cognome", width=320, text_size=16, content_padding=15,
    )
    username_field = ft.TextField(
        label="Username", width=320, text_size=16, content_padding=15,
    )
    email_field = ft.TextField(
        label="Email", width=320, keyboard_type=ft.KeyboardType.EMAIL,
        text_size=16, content_padding=15,
    )
    password_field = ft.TextField(
        label="Password", password=True, can_reveal_password=True,
        width=320, text_size=16, content_padding=15,
    )
    password2_field = ft.TextField(
        label="Conferma password", password=True, can_reveal_password=True,
        width=320, text_size=16, content_padding=15,
    )

    async def do_register(e):
        error_text.visible = False
        loading.visible = True
        page.update()

        first_name = first_name_field.value.strip()
        last_name = last_name_field.value.strip()
        username = username_field.value.strip()
        email = email_field.value.strip()
        password = password_field.value
        password2 = password2_field.value

        # Validazione
        if not username or not email or not password:
            error_text.value = "Username, email e password sono obbligatori."
            error_text.visible = True
            loading.visible = False
            page.update()
            return

        if password != password2:
            error_text.value = "Le password non coincidono."
            error_text.visible = True
            loading.visible = False
            page.update()
            return

        if len(password) < 8:
            error_text.value = "La password deve essere di almeno 8 caratteri."
            error_text.visible = True
            loading.visible = False
            page.update()
            return

        # Registrazione
        success, message = api.register(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        if not success:
            error_text.value = message
            error_text.visible = True
            loading.visible = False
            page.update()
            return

        # Registrazione riuscita → login automatico
        login_success, login_data = api.login(username, password)
        loading.visible = False

        if login_success:
            await prefs.set("auth_token", login_data["access_token"])
            await prefs.set("user_id", login_data["user_id"])
            await prefs.set("username", login_data["username"])
            on_success(login_data)
        else:
            error_text.value = "Registrazione riuscita, ma il login automatico è fallito. Prova ad accedere manualmente."
            error_text.visible = True
            page.update()
    register_button = ft.Button(
        content=ft.Text("Registrati", size=16, weight=ft.FontWeight.BOLD),
        width=320,
        height=50,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BROWN_700,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=do_register,
    )

    password2_field.on_submit = do_register

    login_link = ft.TextButton(
        content=ft.Text("Hai già un account? Accedi", size=14),
        on_click=lambda e: on_login_click(),
    )

    back_link = ft.TextButton(
        content=ft.Text("← Torna indietro", size=14),
        on_click=lambda e: on_back(),
    )

    card = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.PERSON_ADD_OUTLINED, size=60,
                    color=ft.Colors.BROWN_700),
            ft.Text("Crea il tuo account", size=24, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BROWN_700),
            ft.Text("Registrati per completare l'ordine", size=13,
                    color=ft.Colors.GREY_600),
            ft.Container(height=20),
            first_name_field,
            ft.Container(height=10),
            last_name_field,
            ft.Container(height=10),
            username_field,
            ft.Container(height=10),
            email_field,
            ft.Container(height=10),
            password_field,
            ft.Container(height=10),
            password2_field,
            ft.Container(height=5),
            error_text,
            ft.Container(height=10),
            ft.Row([loading], alignment=ft.MainAxisAlignment.CENTER),
            register_button,
            ft.Container(height=10),
            login_link,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=5),
        padding=30,
        bgcolor=ft.Colors.WHITE,
        border_radius=12,
        shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.GREY_300),
    )

    return ft.Container(
        content=ft.Column([
            back_link,
            ft.Container(height=20),
            ft.Row([card], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=0),
        padding=20,
        alignment=ft.Alignment.TOP_CENTER,
    )