import flet as ft
import asyncio
from datetime import datetime
from live_view import live_view
from about_dialog import show_about_dialog

class RealTimeClock(ft.Text):
    def __init__(self):
        super().__init__(
            value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # current time (زمان فعلی)
            size=20,
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.BOLD,
        )

    def did_mount(self):
        self.running = True
        self.page.run_task(self.update_clock)

    def will_unmount(self):
        self.running = False

    async def update_clock(self):
        while self.running:
            self.value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.update()
            await asyncio.sleep(1)

def main_view(page: ft.Page):
    page.bgcolor = "#090B7C"
    page.padding = 20

    clock = RealTimeClock()

    logo = ft.Image(
        src="logo.png",
        width=280,
        fit=ft.ImageFit.CONTAIN,
    )

    # Live container
    live = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.TV, size=128, color=ft.Colors.WHITE),
                ft.Text("LIVE", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        height=350,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.Colors.TEAL_ACCENT_400, ft.Colors.LIGHT_BLUE_ACCENT_700],
        ),
        border_radius=10,
        alignment=ft.alignment.center,
        padding=10,
        on_click=lambda e: live_view(page),
    )

    movie = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.PLAYLIST_PLAY, size=128, color=ft.Colors.WHITE),
                ft.Text("Movies", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        height=250,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#D41E57", "#F1953E"],
        ),
        border_radius=10,
        alignment=ft.alignment.center,
        padding=10,
        col={"xs": 12, "sm": 6},
    )

    series = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.PLAYLIST_PLAY, size=128, color=ft.Colors.WHITE),
                ft.Text("SERIES", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        height=250,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#A832AD", "#5396DD"],
        ),
        border_radius=10,
        alignment=ft.alignment.center,
        padding=10,
        col={"xs": 12, "sm": 6},
    )

    movie_series_row = ft.ResponsiveRow(
        controls=[movie, series],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
    )

    about = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.ROUNDABOUT_LEFT, size=64, color=ft.Colors.WHITE),
                ft.Text("ABOUT US", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        height=80,
        bgcolor=ft.Colors.GREEN_100,
        border_radius=10,
        alignment=ft.alignment.center,
        padding=10,
        on_click=lambda e: show_about_dialog(page),
        col={"xs": 12, "sm": 4},  # full width on extra small; one third on small+
    )

    account = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.INFO, size=64, color=ft.Colors.WHITE),
                ft.Text("ACCOUNT", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        height=80,
        bgcolor=ft.Colors.GREEN_100,
        border_radius=10,
        alignment=ft.alignment.center,
        padding=10,
        col={"xs": 12, "sm": 4},
    )

    # Update Channel container with responsive column settings
    update_list = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.UPDATE, size=64, color=ft.Colors.WHITE),
                ft.Text("UPDATE CHANNEL", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        height=80,
        bgcolor=ft.Colors.GREEN_100,
        border_radius=10,
        alignment=ft.alignment.center,
        padding=10,
        col={"xs": 12, "sm": 4},
    )

    # Responsive row for info containers
    info_row = ft.ResponsiveRow(
        controls=[about, account, update_list],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
    )

    # Header row with logo and clock
    header_row = ft.ResponsiveRow(
        controls=[
            ft.Container(content=logo, alignment=ft.alignment.center_left, col={"xs": 6}),
            ft.Container(content=clock, alignment=ft.alignment.center_right, expand=True, col={"xs": 6}),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        spacing=20,
    )

    # Master row: left part (live) and right part (movie/series and info)
    master_row = ft.ResponsiveRow(
        controls=[
            ft.Container(content=live, col={"xs": 12, "md": 6}),
            ft.Container(
                content=ft.Column(
                    [
                        movie_series_row,
                        info_row,
                    ],
                    spacing=20,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                col={"xs": 12, "md": 6},
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
    )

    content = ft.Column(
        [
            header_row,
            master_row,
        ],
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
        expand=True,
    )

    page.controls.clear()
    page.controls.append(content)
    page.update()

async def main(page: ft.Page):
    page.title = "Smarters Player Lite"
    page.scroll = ft.ScrollMode.AUTO
    page.main_view = lambda: main_view(page)
    main_view(page)

ft.app(target=main)
