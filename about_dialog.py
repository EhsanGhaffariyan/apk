import flet as ft

def show_about_dialog(page: ft.Page):
    dialog = ft.AlertDialog(
        title=ft.Text("About Us", color=ft.Colors.WHITE, size=24, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            [
                ft.Text("Creator: Your Name", color=ft.Colors.WHITE, size=18),
                ft.Text("Company: xAI", color=ft.Colors.WHITE, size=18),
                ft.Text("Version: 1.0.0", color=ft.Colors.WHITE, size=18),
                ft.Text("Contact: example@email.com", color=ft.Colors.WHITE, size=18),
            ],
            spacing=10,
        ),
        actions_alignment=ft.MainAxisAlignment.END,
        bgcolor=ft.Colors.BLUE_GREY_900,
    )


    page.overlay.append(dialog)
    dialog.open = True
    page.update()