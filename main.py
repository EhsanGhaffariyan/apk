import flet as ft
import asyncio
import requests
from datetime import datetime
from flet_video import Video, VideoMedia

class RealTimeClock(ft.Text):
    def __init__(self):
        super().__init__(
            value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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

def show_about_dialog(page: ft.Page):
    dialog = ft.AlertDialog(
        title=ft.Text("About Us", color=ft.Colors.WHITE, size=24, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            [
                ft.Text("Creator: Ehsan Ghaffariyan", color=ft.Colors.WHITE, size=18),
                ft.Text("Company: Ehsan.agency", color=ft.Colors.WHITE, size=18),
                ft.Text("Version: 1.0.0", color=ft.Colors.WHITE, size=18),
                ft.Text("Contact: info@ehsan.agency", color=ft.Colors.WHITE, size=18),
            ],
            spacing=10,
        ),
        actions_alignment=ft.MainAxisAlignment.END,
        bgcolor=ft.Colors.BLUE_GREY_900,
    )
    page.overlay.append(dialog)
    dialog.open = True
    page.update()

def show_coming_soon_dialog(page: ft.Page):
    dialog = ft.AlertDialog(
        title=ft.Text("Coming Soon", color=ft.Colors.WHITE, size=24, weight=ft.FontWeight.BOLD),
        content=ft.Text("This feature is under development and will be available soon!", color=ft.Colors.WHITE, size=18),
        bgcolor=ft.Colors.BLUE_GREY_900,
        actions=[
            ft.TextButton("OK", on_click=lambda e: close_dialog(page, dialog))
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(dialog)
    dialog.open = True
    page.update()

def close_dialog(page: ft.Page, dialog: ft.AlertDialog):
    dialog.open = False
    page.overlay.remove(dialog)
    page.update()

def live_view(page: ft.Page):
    page.title = "Country Channel Selector"
    page.scroll = "auto"
    page.bgcolor = "#090B7C"
    page.padding = 20

    loading_ring = ft.ProgressRing(visible=True)
    page.add(loading_ring)

    countries_url = 'https://iptv-org.github.io/api/countries.json'
    try:
        countries_response = requests.get(countries_url)
        countries_response.raise_for_status()
        countries_data = countries_response.json()
    except requests.RequestException as e:
        page.add(ft.Text(f"Error fetching countries data: {e}", color=ft.Colors.WHITE))
        return

    name_to_code = {country["name"]: country["code"].lower() for country in countries_data}

    m3u_url = 'https://iptv-org.github.io/iptv/index.country.m3u'
    try:
        m3u_response = requests.get(m3u_url)
        m3u_response.raise_for_status()
        m3u_content = m3u_response.text
    except requests.RequestException as e:
        page.add(ft.Text(f"Error fetching M3U file: {e}", color=ft.Colors.WHITE))
        return

    country_channels = {}
    lines = m3u_content.splitlines()
    for i in range(len(lines)):
        line = lines[i]
        if line.startswith('#EXTINF'):
            parts = line.split('group-title="')
            if len(parts) > 1:
                country = parts[1].split('"')[0]
                channel_name = line.split(',', 1)[1] if ',' in line else "Unnamed Channel"
                logo = line.split('tvg-logo="')[1].split('"')[0] if 'tvg-logo="' in line else "https://via.placeholder.com/64"
                url = lines[i + 1].strip() if (i + 1 < len(lines) and not lines[i + 1].startswith('#')) else ""
                if country not in country_channels:
                    country_channels[country] = []
                country_channels[country].append({"name": channel_name, "logo": logo, "url": url})

    loading_ring.visible = False
    page.update()

    top_bar = ft.Row(
        controls=[
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color=ft.Colors.WHITE,
                on_click=lambda e: main_view(page),
            ),
            ft.Image(src="https://store-images.s-microsoft.com/image/apps.16279.13585032091773240.4bccec73-8553-4cf4-9cd6-1461f6ab35d9.36817858-a9fd-4617-af4e-7dd2aca3c698?h=210", height=40)
        ],
        alignment=ft.MainAxisAlignment.START,
        spacing=10
    )

    country_grid = ft.GridView(
        runs_count=9,
        child_aspect_ratio=0.8,
        spacing=10,
        padding=10,
        expand=True,
    )

    for country in sorted(country_channels.keys()):
        code = name_to_code.get(country)
        flag_url = f"https://flagcdn.com/36x27/{code}.png"
        country_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Image(src=flag_url, width=36, height=27),
                    ft.Text(country, size=16, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5
            ),
            padding=5,
            bgcolor=ft.Colors.BLUE,
            border_radius=5,
            alignment=ft.alignment.center,
            on_click=lambda e, cnt=country: show_country_channels(page, cnt, country_channels[cnt]),
        )
        country_grid.controls.append(country_container)

    page_content = ft.Column(
        controls=[
            top_bar,
            country_grid
        ],
        spacing=20,
        expand=True
    )

    page.controls.clear()
    page.controls.append(page_content)
    page.update()

def show_country_channels(page: ft.Page, country: str, channels: list):
    page.title = f"Channels - {country}"
    page.bgcolor = "#090B7C"
    page.padding = 20
    page.scroll = None  # غیرفعال کردن اسکرول کل صفحه

    def show_message(message):
        page.snackbar = ft.SnackBar(content=ft.Text(message))
        page.update()

    if not channels:
        page.add(ft.Text(f"No channels found for {country}", color=ft.Colors.WHITE))
        page.update()
        return

    top_bar = ft.Row(
        controls=[
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color=ft.Colors.WHITE,
                on_click=lambda e: live_view(page),
            ),
            ft.Text(f"{country}", size=20, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
        ],
        alignment=ft.MainAxisAlignment.START,
        spacing=10
    )

    search_field = ft.TextField(
        label="Search Channels",
        width=300,
        bgcolor=ft.Colors.WHITE,
        color=ft.Colors.BLACK,
        on_change=lambda e: update_channel_list(e.control.value)
    )

    progress_bar = ft.ProgressBar(
        width=200,
        color=ft.Colors.BLUE,
        bgcolor=ft.Colors.GREY_800,
        visible=True
    )

    video_player = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Select a channel to play", color=ft.Colors.WHITE, size=16),
                progress_bar
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        bgcolor=ft.Colors.BLACK,
        border_radius=10,
        alignment=ft.alignment.center,
        col={"xs": 12, "md": 8}
    )

    channel_grid = ft.GridView(
        runs_count=4,
        child_aspect_ratio=0.8,
        spacing=10,
        padding=10,
    )

    scrollable_channel_column = ft.Column(
        controls=[channel_grid],
        scroll=ft.ScrollMode.AUTO,
        col={"xs": 12, "md": 4}
    )

    def update_channel_list(search_query: str):
        channel_grid.controls.clear()
        filtered_channels = [
            channel for channel in channels
            if search_query.lower() in channel["name"].lower() or not search_query
        ]
        for channel in filtered_channels:
            logo_src = channel["logo"] if channel["logo"] and channel["logo"].strip() else "https://via.placeholder.com/64"
            def play_channel(e, url=channel["url"]):
                progress_bar.visible = True
                video_player.content = ft.Column(
                    controls=[progress_bar],
                    alignment=ft.MainAxisAlignment.CENTER
                )
                page.update()

                video_player.content = Video(
                    expand=True,
                    playlist=[VideoMedia(url)],
                    playlist_mode=ft.PlaylistMode.LOOP,
                    autoplay=True,
                    volume=100,
                    aspect_ratio=16/9,
                    show_controls=True,
                    filter_quality=ft.FilterQuality.HIGH,
                    muted=False,
                    on_enter_fullscreen=lambda e: show_message("Video entered fullscreen!"),
                    on_exit_fullscreen=lambda e: show_message("Video exited fullscreen!"),
                    on_loaded=lambda e: (
                        setattr(progress_bar, "visible", False),
                        page.update()
                    ),
                    on_error=lambda e: (
                        setattr(video_player, "content", ft.Text(f"Playback error: {e.data}", color=ft.Colors.RED)),
                        page.update()
                    )
                )
                page.update()

            channel_container = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Image(src=logo_src, width=64, height=64, fit=ft.ImageFit.COVER),
                        ft.Text(channel["name"], size=14, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5
                ),
                padding=5,
                bgcolor=ft.Colors.GREY_900,
                border_radius=10,
                alignment=ft.alignment.center,
                on_click=play_channel
            )
            channel_grid.controls.append(channel_container)
        page.update()

    update_channel_list("")

    page_content = ft.Column(
        controls=[
            top_bar,
            ft.Row(
                controls=[search_field],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            ),
            ft.ResponsiveRow(
                controls=[
                    scrollable_channel_column,  # استفاده از Column اسکرول‌دار
                    video_player
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
                expand=True
            )
        ],
        spacing=20,
        expand=True
    )

    page.controls.clear()
    page.controls.append(page_content)
    page.update()

def main_view(page: ft.Page):
    page.bgcolor = "#090B7C"
    page.padding = 20

    clock = RealTimeClock()

    logo = ft.Image(
        src="https://store-images.s-microsoft.com/image/apps.16279.13585032091773240.4bccec73-8553-4cf4-9cd6-1461f6ab35d9.36817858-a9fd-4617-af4e-7dd2aca3c698?h=210",
        width=128,
        border_radius=10,
        fit=ft.ImageFit.CONTAIN,
    )

    live = ft.Container(
        content=ft.Column(
            [
                ft.Image(src="https://img.icons8.com/?size=100&id=46904&format=png&color=000000"),
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
                ft.Image(src='https://img.icons8.com/?size=100&id=lEV2xeBg4PUI&format=png&color=000000'),
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
        on_click=lambda e: show_coming_soon_dialog(page)
    )

    series = ft.Container(
        content=ft.Column(
            [
                ft.Image(src='https://img.icons8.com/?size=100&id=OvABhYotmkFx&format=png&color=000000'),
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
        on_click=lambda e: show_coming_soon_dialog(page)
    )

    movie_series_row = ft.ResponsiveRow(
        controls=[movie, series],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
    )

    about = ft.Container(
        content=ft.Row(
            [
                ft.Image(src='https://img.icons8.com/?size=100&id=83180&format=png&color=FFFFFF'),
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
        col={"xs": 12, "sm": 4},
    )

    account = ft.Container(
        content=ft.Row(
            [
                ft.Image(src='https://img.icons8.com/?size=100&id=85390&format=png&color=FFFFFF'),
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

    update_list = ft.Container(
        content=ft.Row(
            [
                ft.Image(src='https://img.icons8.com/?size=100&id=7421&format=png&color=FFFFFF'),
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

    info_row = ft.ResponsiveRow(
        controls=[about, account, update_list],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
    )

    header_row = ft.ResponsiveRow(
        controls=[
            ft.Container(content=logo, alignment=ft.alignment.center_left, col={"xs": 6}),
            ft.Container(content=clock, alignment=ft.alignment.center_right, expand=True, col={"xs": 6}),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        spacing=20,
    )

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

if __name__ == "__main__":
    ft.app(target=main)
